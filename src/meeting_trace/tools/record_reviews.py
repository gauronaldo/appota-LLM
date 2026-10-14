"""Persist read-based author reviews, explicitly delegated to Codex/AI.

This is a human-readable assessment record, not a model judge or automatic
replacement for fixture scores. No inference, output repair or gold editing.
"""
import argparse
import json
from datetime import datetime, timezone

from ..config import PATHS
from ..evaluation.revalidate import canonical_hash
from ..evaluation.runner import dump

RUBRIC=dict(version='author-read-1.0',reviewer='Codex/AI được tác giả ủy quyền',
    independent=False,human_performed=False,
    source='Đọc toàn transcript, kỳ vọng, items và candidates bị guard chặn; không hỏi Qwen để chấm.',
    semantic_pass='Đủ thông tin chính theo kỳ vọng, đúng đối tượng/kết luận cuối/loại/trạng thái/điều kiện/người/hạn, không có dữ liệu không được nguồn hỗ trợ.',
    format='Tên chủ đề cùng đối tượng, cách viết số tương đương hoặc tiền tố hạn khi quan hệ trước/sau vẫn được giữ trong content/evidence; trường thừa chỉ là schema nếu không đổi nghĩa.',
    state='Giữ phân biệt confirmed/needs_confirmation/unresolved/insufficient_information theo quy ước sản phẩm, không gộp trạng thái sau khi xem output.',
    quarantine='Có thể ghi nội dung candidate đúng nhưng bị chặn schema; semantic_pass không có nghĩa item được chấp nhận hoặc dùng được ngay.',
    ready='ready_without_edit là đạt hợp đồng fixture đầy đủ không cần chuẩn hóa; không đo việc người dùng đã duyệt/xuất qua UI.',
    extras='Không tự coi mọi thông tin ngoài gold là bịa: xem nguồn và tính hữu ích; ghi thiếu phạm vi gold nếu có. Không sửa gold.',
    use='Không đổi điểm tự động; không chỉnh output; đánh giá không độc lập và không thay cho PM/dữ liệu thật.')

# Completed after actually reading all 20 transcripts and preserved C outputs.
PIPELINE_V2=[
('01_change_ab',False,False,'Định dạng + ngữ nghĩa','Candidate chọn B đúng nhưng gắn owner Lan vào decision; mất việc cấu hình tại T16 và không giữ đề xuất A. Không thể coi chỉ là lỗi định dạng.'),
('02_change_aba',True,True,'Đạt','T15 chốt lại sáng thứ Năm; evidence/history giữ T2, T8, T15. Không nâng lịch chiều thành kết luận cuối.'),
('03_switch_condition',False,False,'Ngữ nghĩa','Giữ B và điều kiện ở T12, nhưng gắn chủ đề lưu trữ thay cho lựa chọn dịch vụ email T1; tạo candidate ký hợp đồng từ câu chưa ký T17. Câu hỏi pháp chế là thông tin có thật, không tự coi nó là hallucination.'),
('04_interleaved',False,False,'Ngữ nghĩa','Nhận đúng B thuộc lưu trữ T15, nhưng lịch demo còn mở T8/T17 bị ghi thành issue và mất phương án chiều thứ Tư trong content.'),
('05_unnamed_reversal',False,False,'Hệ thống','Model output bị cắt; không có kết quả để nhận là hiểu đúng. Parser đã nhận input không nhãn.'),
('06_ambiguous_ok',False,False,'Ngữ nghĩa','T13 chưa chốt ví điện tử; output ghi đề xuất ví thành issue và giữ thanh toán cũ thành decision. Chưa thể hiện đúng nội dung chưa chốt chính.'),
('07_let_me_check',False,False,'Ngữ nghĩa','Không bịa việc sửa là điểm tốt, nhưng thiếu blocker chưa tái hiện T12 và thiếu trạng thái/diễn biến xem lỗi chưa được giao T4/T10. Chưa biết nguyên nhân không đồng nghĩa chưa tái hiện.'),
('08_self_commit_label',False,False,'Định dạng + ngữ nghĩa','Đúng lời xem lỗi/báo chiều nay T8, nhưng status confirmed với owner null thay cho needs_confirmation; due cũng bị mất khỏi trường cấu trúc. Guard chặn.'),
('09_named_assignee_no_speaker',True,False,'Định dạng','T9 giao Lan gửi báo cáo trước thứ Sáu; output giữ đúng người/việc/hạn/phần ghi chú. due có tiền tố trước khác quy ước fixture, không đổi nghĩa deadline.'),
('10_indirect_consensus',True,False,'Định dạng','T7/T13 đồng thuận dùng một cột. Màn hình báo cáo là tên cụ thể của đối tượng báo cáo, không phải nhầm sang một chủ đề khác.'),
('11_unresolved_budget',False,False,'Ngữ nghĩa','Content hoãn lựa chọn là đúng và không tạo việc chuyển dữ liệu, nhưng status needs_confirmation thay unresolved khác quy ước trạng thái đã chọn cho nội dung rõ ràng chưa chốt.'),
('12_reopen_confirmed',False,False,'Ngữ nghĩa','Giữ câu hoãn T12 nhưng type decision thay unresolved. Issue hoàn tiền có bằng chứng T6, không phạt chỉ vì gold chưa liệt kê; lỗi chính vẫn là loại của kết luận mở lại.'),
('13_speakerless_pending',False,False,'Định dạng + ngữ nghĩa','Tên cách xuất báo cáo là cùng đối tượng; content chưa thống nhất đúng T12. Tuy nhiên status needs_confirmation thay unresolved vẫn là sai trạng thái, không tính toàn case đạt.'),
('14_request_not_assignment',False,False,'Ngữ nghĩa','Không biến yêu cầu thành assignment là đúng, nhưng mất nội dung bộ lọc theo tháng T2 và câu chưa thống nhất trường thời gian T12; chỉ còn một issue chung chung.'),
('15_conditional_task',False,False,'Ngữ nghĩa','Giữ vấn đề quyền truy cập, nhưng bỏ công việc Lan nhận kiểm tra hoàn tiền khi có sandbox T6. Ba issue không thay thế action có điều kiện.'),
('16_clear_decision',True,False,'Định dạng/schema','Candidate giữ đúng quyết định phát hành 2.1 vào thứ Hai T11. due không được phép nằm trên decision nên bị guard chặn; thời điểm đó có thật, không phải ngày bịa. Ngữ nghĩa candidate đúng nhưng chưa dùng được.'),
('17_clear_assignment',False,False,'Định dạng + ngữ nghĩa','Đúng biểu đồ đường và giữ người nhận Lan, nhưng mất phản hồi nhãn chữ T7; sai status việc tài liệu đã nhận T9; mất due T13 và ghi phân quyền chưa chốt thành issue.'),
('18_anonymous_assignment',False,False,'Ngữ nghĩa','Công việc có thật T6, nhưng owner Người nói 2 không phải danh tính; status confirmed sai với actor chưa biết. Guard chặn trước khi xuất.'),
('19_speakerless_commitment',False,False,'Ngữ nghĩa','Công việc/hạn có nguồn T5, nhưng owner Speaker null (T5) là định danh tự tạo; cần null và needs_confirmation. Guard chặn.'),
('20_explicit_name_in_content',True,False,'Định dạng','Huy giao Mai ở T9, Mai xác nhận T10. Output đúng Mai/việc/hạn; báo cáo tháng và báo cáo cùng đối tượng, chỉ khác tên topic so với fixture.')]


BASELINE_V2=[
('01_change_ab',True,False,'Định dạng/schema','Giữ B cuối ở T13/T14 và lịch sử bỏ máy chủ riêng. Candidate Lan nhận cấu hình trước thứ Sáu có cả tên/hạn trong content và evidence T15/T16, nhưng owner/due để null nên bị chặn. Đúng nghĩa candidate, chưa đủ trường cấu trúc.'),
('02_change_aba',False,False,'Ngữ nghĩa','Câu sáng thứ Năm trùng kết luận cuối, nhưng evidence chỉ đến T8: tại đó đã đổi sang chiều. Không dẫn T15 chốt lại sáng, nên đúng câu chưa chứng minh được hiểu lần đảo cuối.'),
('03_switch_condition',False,False,'Ngữ nghĩa','Giữ điều kiện pháp chế nhưng ghi lựa chọn B thành unresolved/unresolved thay cho quyết định có điều kiện. Không gộp hai loại này sau khi xem output.'),
('04_interleaved',True,False,'Định dạng','Giữ B cho lưu trữ và đề xuất demo chiều thứ Tư ở trạng thái unresolved, evidence có T17 còn mở. Lịch trình bày/lịch demo là cùng đối tượng; tên topic khác fixture.'),
('05_unnamed_reversal',False,False,'Định dạng + ngữ nghĩa','Giữ cổng B đúng T14 nhưng biến chính sách giữ A cho giao dịch cũ thành action mới và giả định có lỗi thành issue; nội dung phụ trả bằng tiếng Trung. Không tính chỉ một quyết định đúng là cả case đạt.'),
('06_ambiguous_ok',False,False,'Định dạng + ngữ nghĩa','Hai candidates không có evidence/reason; đề xuất ví chưa chốt bị ghi thành issue. Không có bản ghi đầy đủ cho nội dung mở chính.'),
('07_let_me_check',False,False,'Ngữ nghĩa','Giữ blocker chưa tái hiện, nhưng status unresolved khác needs_confirmation và bỏ nội dung điều tra chưa được giao. Không bịa sửa lỗi là điểm tốt, chưa đủ cả case.'),
('08_self_commit_label',False,False,'Ngữ nghĩa','Lời nhận xem lỗi/báo chiều nay bị ghi issue/confirmed thay action/needs_confirmation khi danh tính chưa biết. Hạn cũng chưa vào trường due.'),
('09_named_assignee_no_speaker',True,False,'Định dạng/schema','Candidate giữ đúng Lan, báo cáo và trước thứ Sáu trong content; evidence T9 giao việc có thật. due null và reason trống làm guard chặn, cần chuẩn hóa trường thay vì suy luận thêm việc mới.'),
('10_indirect_consensus',True,False,'Định dạng','Giữ một cột, dữ liệu không đổi, evidence bao gồm T13 đồng thuận cuối. Topic dài hơn báo cáo nhưng cùng màn hình điện thoại.'),
('11_unresolved_budget',True,False,'Định dạng','Giữ hoãn chọn hạ tầng đến khi đủ báo giá ở unresolved/unresolved và evidence T13. Không tạo assignment chuyển dữ liệu; chỉ khác tên topic.'),
('12_reopen_confirmed',False,False,'Ngữ nghĩa','Candidate vẫn giữ câu phát hành thứ Hai từ T3, dù evidence có T12 hoãn. unresolved/confirmed mâu thuẫn và bị chặn; không phải chỉ lỗi viết tên topic. Issue hoàn tiền có nguồn.'),
('13_speakerless_pending',True,False,'Định dạng','Ghi cần hiểu mục đích trước khi quyết định cách tải với unresolved/unresolved; evidence T12 nêu chưa thống nhất. Nội dung cùng câu hỏi mở, khác chuỗi chưa thống nhất và tên topic fixture.'),
('14_request_not_assignment',False,False,'Định dạng + ngữ nghĩa','Candidate giữ yêu cầu bộ lọc nhưng gán issue, không evidence và thiếu câu chưa chọn trường thời gian T12. Không tạo assignment là đúng nhưng chưa đủ trích xuất.'),
('15_conditional_task',False,False,'Ngữ nghĩa','Bỏ lời Lan nhận kiểm tra hoàn tiền khi có sandbox T6; giữ blocker nhưng confirmed sai quy ước, thêm nội dung tiếng Trung. Không thay action có điều kiện bằng câu bàn lại cách thử.'),
('16_clear_decision',True,False,'Định dạng','Quyết định 2.1 thứ Hai có evidence T11/T12, owner/due null hợp schema. Topic Phát hành bản 2.1 khác tên ngắn của fixture.'),
('17_clear_assignment',False,False,'Định dạng + ngữ nghĩa','Có biểu đồ đường và audit trước thứ Hai; mất phản hồi chữ nhỏ, owner Lan không vào trường, sandbox và phân quyền sai loại/trạng thái. Case nhiều nhóm chưa đủ.'),
('18_anonymous_assignment',False,False,'Ngữ nghĩa','Người nói 2 được dùng làm owner/confirmed; đây là nhãn chứ chưa phải danh tính. Guard chặn, cần giữ null và needs_confirmation.'),
('19_speakerless_commitment',False,False,'Ngữ nghĩa','Giữ việc thay ảnh/hạn nhưng confirmed với owner null sai khi không xác định người nói. Guard chặn, chưa giải quyết bất định danh tính.'),
('20_explicit_name_in_content',True,False,'Định dạng','Mai gửi báo cáo đúng T9/T10, hạn thứ Sáu đúng và không tạo việc đối soát mới. Topic dài hơn báo cáo, không nhầm đối tượng.')]

FRESH_BASELINE=[
('H01_reminders',True,False,'Định dạng','Giữ đúng thông báo trong ứng dụng chỉ cho lịch xác nhận T15, lịch sử SMS bị bỏ T3/T6. Topic nhắn lịch là cách viết lệch của nhắc lịch, cùng đối tượng.'),
('H02_conditional_export',False,False,'Ngữ nghĩa','Giữ điều kiện trong content nhưng action confirmed thay needs_confirmation; bỏ phản hồi CSV mã hóa và blocker pháp chế. Không chỉ sai tiền tố deadline.'),
('H03_reopened_backup',False,False,'Ngữ nghĩa','Giữ chưa chốt số ngày và không hồi sinh 30 ngày, nhưng bỏ issue thiếu dung lượng T11. Lịch sử có T3/T12 nhưng thiếu lần đề xuất 14 ngày trong history.'),
('H04_discount_request',False,False,'Ngữ nghĩa','Giữ câu chưa chốt tăng, nhưng bỏ phản hồi 20% và công việc Huy nhận có điều kiện T11. Một câu unresolved chưa bao phủ ba nhóm kỳ vọng.'),
('H05_webhook_limit',False,False,'Định dạng + ngữ nghĩa','Quyết định giới hạn đúng và giữ mọi điều kiện. Action Mai có nguồn T14/T15 nhưng due null và content cũng không giữ thứ Sáu; mất thông tin hạn, không chỉ sai cách viết trường.'),
('H06_unsettled_rota',False,False,'Ngữ nghĩa','Không bịa người trực/assignment, giữ hai phương án ở unresolved; bỏ issue chưa có lịch làm việc T10, nên chưa đủ case.')]

FRESH_PIPELINE=[
('H01_reminders',False,False,'Ngữ nghĩa','Nội dung nhắc lịch và điều kiện đúng T15 nhưng gắn lịch demo, là đối tượng khác; history bỏ diễn biến SMS T3/T6/T7. Verifier cùng model vẫn cho qua.'),
('H02_conditional_export',False,False,'Ngữ nghĩa','Action mất CSV mã hóa và điều kiện pháp chế trong content, confirmed thay needs_confirmation; phản hồi bị bỏ và blocker sai trạng thái. Evidence chứa điều kiện không bù cho content đã bỏ điều kiện.'),
('H03_reopened_backup',False,False,'Ngữ nghĩa','Giữ chưa chốt số ngày, nhưng needs_confirmation thay unresolved và mất issue dung lượng T11. Không dùng đúng một câu nội dung để nhận cả case đạt.'),
('H04_discount_request',False,False,'Ngữ nghĩa','Ghi câu chưa chốt thành action confirmed không owner; guard chặn. Mất phản hồi 20% và việc Huy nhận có điều kiện.'),
('H05_webhook_limit',False,False,'Định dạng + ngữ nghĩa','Giới hạn ba lần/30 giây/thất bại đúng. Việc Mai đã nhận bị để owner/due null và needs_confirmation, content mất thứ Sáu. Thiếu đề xuất gửi vô hạn T2 trong history.'),
('H06_unsettled_rota',False,False,'Ngữ nghĩa','Giữ câu chưa thống nhất nhưng status needs_confirmation thay unresolved, bỏ issue lịch làm việc và diễn biến hai/ba người. Không bịa assignment là điểm tốt.')]


def save_review(suite,arm,assessments):
    rows=[]
    for id,semantic,ready,category,reason in assessments:
        source=PATHS.benchmarks/'comparisons/qwen2.5-7b'/suite/arm/(id+'.json')
        if suite=='v2' and arm=='pipeline': source=PATHS.benchmarks/'results/ollama'/(id+'.json')
        result=json.loads(source.read_text(encoding='utf-8'))
        rows.append(dict(id=id,semantic_pass=semantic,ready_without_edit=ready,
            error_class=category,reason=reason,source=source.relative_to(PATHS.root).as_posix(),
            source_canonical_sha256=canonical_hash(result)))
    data=dict(suite=suite,arm=arm,rubric_version=RUBRIC['version'],
        reviewer=RUBRIC['reviewer'],independent=False,human_performed=False,
        authorized_by_author=True,reviewed_at=datetime.now(timezone.utc).isoformat(),
        total=len(rows),semantic_passed=sum(row['semantic_pass'] for row in rows),cases=rows)
    dump(PATHS.benchmarks/'reviews'/(suite+'_'+arm+'.json'),data)
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    dump(PATHS.benchmarks/'reviews/rubric.json',RUBRIC)
    for suite,arm,rows in [('v2','pipeline',PIPELINE_V2),('v2','baseline_b',BASELINE_V2),
                          ('holdout-v3','baseline_b',FRESH_BASELINE),('holdout-v3','pipeline',FRESH_PIPELINE)]:
        result=save_review(suite,arm,rows)
        print(suite+' / '+arm+': '+str(result['semantic_passed'])+'/'+str(result['total'])+' author-delegated AI reading')


if __name__=='__main__': main()
