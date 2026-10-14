"""Evidence-based diagnostic report; inference and historical scores unchanged."""
import argparse
import json

from ..config import PATHS
from .debugging import BASE, load
from .runner import dump

AUDIT=[
('01_change_ab','Hợp lý: B cuối và Lan nhận cấu hình đều rõ.','Topic triển khai/cấu hình là alias; history yêu cầu đúng ID.','Owner/due null dù content có người/hạn; thiếu history chốt cuối.','Bước 1 bỏ T16, đầu ra thiếu action; decision gắn owner nên guard chặn.'),
('02_change_aba','Hợp lý: đổi sáng → chiều → sáng có lần chốt cuối rõ.','Cần evidence lần chốt cuối, không chỉ đúng chữ sáng.','Content trùng kết luận nhưng không dẫn T15; history dừng trước lần quay lại A.','Đạt toàn case trong lượt lịch sử.'),
('03_switch_condition','Hợp lý: chọn B có điều kiện, pháp chế chưa duyệt.','Gold chỉ một decision, không liệt kê blocker pháp chế có thật.','Ghi lựa chọn có điều kiện thành unresolved; quy ước decision có điều kiện cần rõ.','Topic lưu trữ xuất hiện ở bước 1 và được bước 2 dùng lại; thêm action từ câu chưa ký.'),
('04_interleaved','Hợp lý: hai đối tượng đan xen, B đã chốt, lịch demo còn mở.','Lịch trình bày/lịch demo cùng đối tượng; exact topic phạt alias.','Đúng hai nội dung chính, trượt topic.','Lịch demo bị ghi issue và mất phương án chiều thứ Tư.'),
('05_unnamed_reversal','Hợp lý: không có nhãn nhưng chốt cổng B rõ.','Gold không kiểm tra đầy đủ phạm vi chuyển đổi; lesson cũ còn nói parser chưa hỗ trợ.','Đúng B nhưng thêm action không phải việc mới; có nội dung tiếng Trung.','Lượt lịch sử bị cắt; lượt trace mới hoàn tất cả ba bước. Chưa biết tầng gây cắt cũ.'),
('06_ambiguous_ok','Hợp lý: ok không đủ để chọn ví.','Có thể ghi thêm trạng thái thanh toán cũ có nguồn, nhưng không thay câu chưa chốt ví.','Không evidence/reason; sai loại và mất unresolved chính.','Không giữ đầy đủ câu chưa chốt ví; ghi đề xuất thành issue.'),
('07_let_me_check','Hợp lý: ý định xem chưa phải nhận sửa.','Status issue chưa định nghĩa; unresolved/needs_confirmation cho ý định mơ hồ chưa mô tả rõ.','Giữ blocker nhưng mất câu hỏi về người nhận; sai status theo gold.','Bước 1 bỏ T4; thiếu blocker chưa tái hiện và nội dung chưa giao.'),
('08_self_commit_label','Hợp lý với chính sách không dùng nhãn làm danh tính.','Tách cam kết đã có khỏi danh tính chưa biết sẽ rõ hơn một status chung.','Task bị đổi thành issue; mất trường due; confirmed không hợp chính sách actor.','Nội dung việc có nhưng confirmed với owner null; guard chặn.'),
('09_named_assignee_no_speaker','Hợp lý: tên Lan nằm trong lời giao.','Tiền tố trước làm lệch due dù quan hệ deadline được giữ.','Candidate đúng câu/người/hạn nhưng due null và reason trống.','Đúng ngữ nghĩa; lỗi chuẩn hóa due trước thứ Sáu.'),
('10_indirect_consensus','Hợp lý: nhiều lượt đồng thuận dùng một cột.','Topic báo cáo/màn hình báo cáo là alias.','Đúng nghĩa, trượt exact topic.','Đúng nghĩa, trượt exact topic.'),
('11_unresolved_budget','Hợp lý: hoãn chọn vì thiếu báo giá.','Cần định nghĩa unresolved so với needs_confirmation; có blocker chưa đủ báo giá ngoài gold.','Đúng nghĩa, trượt topic.','Nội dung hoãn đúng, chỉ status khác gold; không đủ để nói model hiểu sai sự kiện.'),
('12_reopen_confirmed','Hợp lý: lịch phát hành bị mở lại vì vấn đề mới.','Gold bỏ issue hoàn tiền có thật; scorer coi mục dư là lỗi.','Candidate giữ câu chốt cũ; unresolved/confirmed mâu thuẫn.','Giữ hoãn nhưng type decision; issue có nguồn bị phạt thêm vì ngoài gold.'),
('13_speakerless_pending','Hợp lý: cuối họp chưa chọn cách tải.','Khác chuỗi diễn đạt và topic; status chưa định nghĩa đầy đủ.','Đúng câu hỏi mở, khác cách viết và topic.','Nội dung chưa thống nhất đúng, status khác gold; chưa đủ quy trách nhiệm ngữ nghĩa thuần túy.'),
('14_request_not_assignment','Hợp lý: yêu cầu tháng chưa thành việc.','Status request chưa định nghĩa; phản hồi chữ nhỏ cũng có nguồn nhưng gold không liệt kê.','Sai type, không evidence, thiếu câu chưa chọn trường thời gian.','Bước 1 bỏ T2; mất yêu cầu bộ lọc tháng, chỉ còn vấn đề chung.'),
('15_conditional_task','Hợp lý: Lan nhận có điều kiện, sandbox chưa mở.','Gold cần owner Lan; guard không nhận em mới nhận; status issue chưa rõ.','Bỏ action có điều kiện; thông tin sandbox không đủ thay việc.','Candidate thay action bằng issue; oracle Lan đúng cũng bị guard bác.'),
('16_clear_decision','Hợp lý: phát hành 2.1 thứ Hai được chốt rõ.','Ngày trong decision có thật nhưng schema chỉ cho action có due.','Đúng nghĩa, trượt topic dài.','Candidate đúng nghĩa nhưng due trên decision làm guard chặn.'),
('17_clear_assignment','Hợp lý nhưng tải nhiều nhóm: sáu mục trong 24 lượt.','Exact topic, status issue/request chưa rõ; cần chấm theo item thay all-or-nothing.','Thiếu feedback, owner null, sai type/status; thêm định nghĩa contract vẫn chưa hết lỗi.','Bước 1 bỏ feedback T7; sai trạng thái/người/hạn ở nhiều mục.'),
('18_anonymous_assignment','Hợp lý với chính sách không dùng speaker label làm tên thật.','Status trộn độ rõ của việc và danh tính; cần chính sách explicit.','Đặt owner Người nói 2; guard chặn.','Đặt owner Người nói 2; guard chặn.'),
('19_speakerless_commitment','Hợp lý: việc/hạn rõ, người chưa rõ.','Không nên bắt biết tên thật để coi lời nhận việc tồn tại; cần tách actor uncertainty.','Confirmed với owner null; guard chặn.','Tạo owner Speaker null (T5); guard chặn.'),
('20_explicit_name_in_content','Hợp lý: Huy giao Mai, Mai nhận.','Exact topic gây fail; metric invented_owner_due báo hai trường bịa dù đúng nguồn.','Đúng nghĩa, trượt topic.','Đúng nghĩa, trượt topic.'),
('H01_reminders','Hợp lý: bỏ SMS, chọn in-app có giới hạn.','History bắt T2/T7/T15, không chấp nhận chuỗi T3/T6/T15 đã đủ chứng minh đổi kênh; topic typo cũng bị phạt.','Giữ kết luận/điều kiện và đổi kênh đúng, trượt topic và exact history.','Gắn lịch demo cho nhắc lịch; history mất SMS.'),
('H02_conditional_export','Hợp lý: Ngọc chỉ xuất sau pháp chế và phải mã hóa.','Status issue/request chưa rõ, nhưng mất điều kiện là lỗi thật không phụ thuộc ontology.','Bỏ request và blocker; conditional action confirmed.','Bước 1 bỏ request T4; content/reason sai điều kiện và verifier vẫn pass.'),
('H03_reopened_backup','Hợp lý: hủy 30 ngày, chưa chọn số ngày mới.','Status issue chưa rõ; yêu cầu exact history có thể phạt trace khác nhưng cùng nghĩa.','Không hồi sinh 30 ngày nhưng bỏ blocker dung lượng.','Bước 1 bỏ blocker/kết luận cuối; sau đó giữ câu chưa chốt nhưng sai status.'),
('H04_discount_request','Hợp lý: đề nghị 20% chưa chốt và Huy nhận có điều kiện.','Status request chưa định nghĩa; một câu tổng hợp không bao phủ đủ ba nhóm kỳ vọng.','Chỉ còn unresolved; bỏ request 20% và action Huy.','Bước 1 bỏ request/action; câu chưa chốt bị đổi thành action confirmed và bị chặn.'),
('H05_webhook_limit','Hợp lý: giới hạn retry và Mai nhận gửi báo cáo.','Guard không nhận em sẽ gửi; có thể bổ sung T14 nêu tên để qua.','Decision đúng; mất hạn của action trong content/field.','Mất owner/hạn và đổi trạng thái việc đã nhận; history thiếu đề xuất ban đầu.'),
('H06_unsettled_rota','Hợp lý: hai/ba người chưa chọn, chưa có lịch để xếp.','Status issue chưa định nghĩa; cần phân biệt không giao việc với mất blocker.','Không bịa assignment nhưng bỏ blocker lịch làm việc.','Thiếu blocker và trace phương án; nội dung chưa chốt đúng nhưng status khác gold.'),
]


def render():
    offline=load(BASE/'offline.json')
    summary=offline['summary']
    live=[load(p) for p in sorted((BASE/'live').glob('L*.json'))]
    verifier=[load(p) for p in sorted((BASE/'verifier').glob('V*.json'))]
    audit=dict(reviewer='Codex/AI debugging; not independent',not_new_quality_score=True,
        cases=[dict(id=id,input_judgement=source,benchmark_concern=bench,baseline_failure=b,pipeline_failure=c)
               for id,source,bench,b,c in AUDIT])
    dump(BASE/'case_audit.json',audit)
    refs='data/benchmarks/debug/2026-10-14'
    lines=['# Debug nguyên nhân fail — 14/10/2026','',
        '**Có lỗi ở MVP và ở hợp đồng đánh giá; chưa thấy transcript sai là nguyên nhân chính.** '
        'Không thể quy mọi fail cho Qwen 7B. Đã kiểm tra đủ 26 transcript/nhãn và 52 output đã lưu; '
        'thử guard/scorer không dùng model, rồi chạy can thiệp riêng trên Qwen local. Không sửa gold, scorer, '
        'pipeline hay kết quả lịch sử. Đây là chẩn đoán bởi Codex/AI, không gán nhãn độc lập hoặc benchmark chất lượng mới.','',
        '## 1. Tách từng tầng','',
        '| Tầng | Bằng chứng | Kết luận |','| --- | --- | --- |',
        '| Input/parser | 26/26 transcript giữ nguyên nội dung sau tách dòng/tên; phần kết luận/việc trong nguồn có thật. | Parser không giải thích điểm thấp của bộ này; heuristic vẫn có giới hạn ngoài corpus. |',
        '| Nhãn và chính sách | Issue/request luôn needs_confirmation ở gold nhưng prompt không định nghĩa chính sách đó; enum có 4 status mà chưa có bảng áp dụng đầy đủ theo type. | Lỗi hợp đồng giữa nhãn/prompt/schema; không tự gọi mọi lệch status là hiểu sai. |',
        '| Scorer | Bỏ riêng exact topic: B 0 → 5/20, C 1 → 3/20. Bỏ riêng due: C 1 → 2/20; riêng status: C 1 → 2/20. | Điểm case thấp có phần do định dạng; các phép bỏ một tiêu chí không cộng được với nhau và không phải điểm chất lượng. |',
        '| Scorer an toàn | Hai câu phủ định lựa chọn vẫn được chấm đạt; topic alias làm metric báo người/hạn bịa dù có nguồn. | Bộ chấm vừa phạt nhầm vừa có thể cho qua sai nghĩa; precision/recall và invented_owner_due hiện không đo riêng ngữ nghĩa/hallucination. |',
        '| Bước 1 | Thiếu các lượt quan trọng: T16/case01, T7/case17, T4/H02, T11/H04. Đổi duy nhất topic lưu trữ → email làm bước 2 đổi theo. | Có bỏ sót và truyền neo sai; bước 2 vẫn nhận toàn transcript nên không phải hard-filter tất yếu, nhưng chịu ảnh hưởng của topic. |',
        '| Bước 2/model | Owner được viết trong content nhưng field null; thiếu request/action/blocker; thêm contract ở case17 vẫn mất feedback và owner. | Lỗi trích xuất/schema thật; làm rõ prompt giúp một phần, không đủ sửa toàn bộ. |',
        '| Guard code | Mai: Em sẽ gửi bị bác; Em nhận gửi qua. Lan: em mới nhận có điều kiện cũng bị bác. Tên Mai trong câu chưa ai nhận vẫn qua guard. | Regex vừa bác đúng vừa nhận sai; chặn trước verifier có thể làm mất item đúng. |',
        '| Verifier | 32/32 check lịch sử đều pass; probe ba dòng mất điều kiện/mã hóa vẫn pass. Chỉ đổi reason của cùng candidate làm verdict đổi. | Không đủ tin cậy làm cổng an toàn; kiểm tra cùng model và candidate reasoning không độc lập. |',
        '| Provider/log | Case05 trước bị cắt; trace mới cả ba bước stop. Các request debug chỉ 578–2011 input token, output 78–862, dưới giới hạn 8192/4000. | Chưa tái hiện nguyên nhân cắt cũ; không có bằng chứng do context đầy trong các probe này. Log cũ không giữ stage/token/done_reason nên thiếu khả năng truy lỗi. |',
        '| Duyệt/xuất | Gate/revision/audit có test; UI chỉ sửa/xóa mục hiện có, không thêm mục bị model bỏ sót, không sửa history. | Cổng duyệt hoạt động về cơ chế nhưng workflow chưa khôi phục được biên bản đầy đủ; điểm hiện chấm trước duyệt. |','',
        '## 2. Transcript/nhãn có vấn đề gì?','',
        'Các tình huống A → B → A, thiếu người nói, đề nghị chưa giao và việc có điều kiện là hợp lý với đề tuyển dụng. '
        'Khó không đồng nghĩa câu hỏi sai. Corpus tổng hợp chưa chứng minh tính đại diện cuộc họp thật, và vài câu nói về biên bản/đừng tự đặt deadline vẫn mang dấu vết tác giả test. '
        'Đánh giá đủ sáu nhóm ở case17 gây tỷ lệ all-or-nothing thấp: đúng nhiều item vẫn trượt cả case.','',
        'Những điểm cần sửa ở nhãn/hợp đồng trước vòng đánh giá tiếp:','',
        '- Topic là chuỗi tự do nhưng gold bắt đúng một tên; nên định nghĩa ID chủ đề/alias hoặc chấm đối tượng bằng rubric độc lập.',
        '- Tách trạng thái lựa chọn/công việc khỏi độ rõ người nhận và trạng thái người dùng đã duyệt. needs_confirmation của issue rõ có thể là workflow, không phải thiếu bằng chứng.',
        '- Gold có phần thiếu các thông tin hữu ích khác: blocker pháp chế/case03, issue hoàn tiền/case12; scorer phạt mọi item ngoài gold. Cần gán nhãn đầy đủ hoặc có rubric kiểm tra extras có nguồn.',
        '- History yêu cầu đúng turn dù lượt khác đã chứng minh diễn biến: H01 B giữ T3 SMS → T6 bỏ SMS → T15 in-app, nhưng gold muốn T2/T7/T15. Giữ timeline nghĩa đúng, không chỉ checklist ID.',
        '- Due phải bỏ trước theo convention dù transcript có quan hệ trước; cần lưu quan hệ thời gian riêng, không dùng khác tiền tố làm lỗi nghĩa.',
        '- Lesson case05 còn nói parser chưa hỗ trợ là nhận xét lịch sử đã lỗi thời; không dùng mô tả cũ để quy nguyên nhân hiện tại.',
        '- Chấm đọc trước đây cũng giữ status của gold quá cứng. Các case11/13 cần coi là tranh chấp ontology cho đến khi contract rõ, không tự xem là chứng minh model hiểu sai sự kiện. Giữ lịch sử chấm cũ để minh bạch.','',
        'Thử đưa item tổng hợp từ nhãn đúng + câu nguồn qua guard (oracle, **không phải dự đoán model**): '
        'Lan ở case15 và Mai ở H05 bị bác do regex. Với H05, thêm T14 có tên Mai là workaround hợp lệ; '
        'với case15 nguồn có speaker Lan và lời em mới nhận, guard hiện không hiểu lời tự nhận đó. Không sửa nhãn để né lỗi code.','',
        '## 3. Thử nghiệm can thiệp có kiểm soát','',
        'Tất cả dùng qwen2.5:7b Q4_K_M, Ollama 0.32.6, temperature=0, seed=42, context=8192, output=4000; '
        'case đã xem là dữ liệu debug, không nhận là kiểm thử kín. Sáu experiment chính dùng tổng 8 API call; '
        'ba probe verifier dùng 3 call. Một lượt mỗi experiment, không retry chọn output tốt.','',
        '| Thử nghiệm | Thay đổi | Quan sát |','| --- | --- | --- |',
        '| L01 → L02, case03 | Giữ transcript/events/prompt/model/schema; chỉ đổi tên topic đầu vào lưu trữ thành email. | Decision đầu ra chuyển từ lưu trữ sang email nhà cung cấp; content B có điều kiện giữ nguyên. Vẫn tạo action từ câu chưa ký. Chứng minh tác động neo topic, chưa chứng minh sửa hết pipeline. |',
        '| L03 → L04, case17 | Giữ input/model/schema; thêm định nghĩa general status/coverage/field mapping vào prompt B. | Thêm lại issue sandbox ở needs_confirmation; vẫn thiếu feedback chữ nhỏ, owner Lan null và phân quyền bị gắn issue. Can thiệp contract gồm nhiều hướng dẫn, không cô lập riêng status. |',
        '| L05, case05 | Pipeline nguyên bản, chỉ ghi request/response từng stage. | Hoàn tất event → item → verifier, không cắt. Lượt mới khác lượt cũ: chưa thể xác định tầng/điều kiện gây cắt trước đây, không ghi đè kết quả fail. |',
        '| L06, micro một dòng | Mai: Em sẽ gửi báo cáo trước thứ Sáu; B nguyên bản. | Model biết owner Mai/content đúng, nhưng due null, reason trống; guard còn bác lời sẽ gửi. Cả model field mapping và code có lỗi ngay trên dữ liệu rõ. |',
        '| V01, phủ định giao việc | Mai đang nghỉ, chưa ai nhận; candidate bịa Mai được giao. | Verifier bác đúng, cho thấy không phải mọi probe đều bị cho qua. |',
        '| V02, mất điều kiện | Nguồn CSV mã hóa sau pháp chế; candidate gửi CSV với confirmed, bỏ điều kiện/mã hóa. | Verifier cho pass cả năm tiêu chí ngay với nguồn ba dòng; reason lấy điều kiện từ evidence để bù cho content thiếu. Đây là lỗi thật. |',
        '| V02 → V03 | Chỉ đổi candidate.reason sang câu pháp chế đã duyệt. Content/evidence/owner/due/status giữ nguyên. | Verdict chuyển từ pass sang fail. Reason không nên quyết định mức hỗ trợ của các field; lý do fail mới vẫn có phần sai về owner/due. Một cặp nhỏ, không suy ra tỷ lệ chung. |','',
        '28/32 reason verifier lịch sử dài hơn 300 ký tự, 3 có chữ Trung, 3 lặp hướng dẫn prompt. '
        'Đây là triệu chứng model tạo giải thích theo khuôn thay vì kiểm tra nhất quán, không phải bằng chứng duy nhất về nguyên nhân nội bộ model. '
        'Prompt C còn chứa yêu cầu viết quote rồi bổ sung yêu cầu không xuất quote; đây là nhiễu thiết kế cần dọn, nhưng chưa có ablation chứng minh nó gây từng lỗi.','',
        '## 4. Audit từng case','',
        'Các nguyên nhân có thể đồng thời xuất hiện; không gán phần trăm trách nhiệm khi chưa có phép đo độc lập. '
        'Thiếu ID trong bước 1/candidate là proxy quan sát, không tự chứng minh item bị mất vì có thể dùng evidence tương đương.','',
        '| Case | Input/nhãn | Lỗi B | Lỗi C | Vấn đề đánh giá |',
        '| --- | --- | --- | --- | --- |']
    for id,source,bench,b,c in AUDIT:
        lines.append(f'| {id} | {source} | {b} | {c} | {bench} |')
    lines += ['', '## 5. Thứ tự sửa dựa trên nguyên nhân', '',
        '1. Chốt contract type/status/condition/actor/time trước. Viết rubric và gán nhãn phiên mới trước khi chạy; giữ nguyên v2/v3 làm lịch sử. Chấm từng item/field, fail cả case vẫn là một chỉ số phụ.',
        '2. Sửa guard nhận lời tự nhận tự nhiên và phân biệt tên được nhắc với người được giao. Không coi name substring là bằng chứng giao việc; giữ null/ẩn danh khi chưa biết.',
        '3. Bỏ phụ thuộc cứng vào verdict cùng model: checker phải chỉ ra condition/giới hạn trong nguồn và field nào của content giữ nó, kiểm tra phần còn thiếu và các lượt hủy sau evidence; không dùng reason extractor như bằng chứng. Cần probe đối kháng cho từng tiêu chí.',
        '4. Rút prompt/schema theo nhiệm vụ, dọn chỉ dẫn quote mâu thuẫn; thử extraction trực tiếp rồi mới quyết định giữ tầng gom chủ đề. Nếu giữ, kiểm tra coverage và cho bước sau bác topic/events sai. Không áp dụng topic rename từ gold vào pipeline thật.',
        '5. Cho người duyệt thêm item thiếu và sửa history; hiện edit/remove không đủ. Đo chất lượng/thời gian sau duyệt riêng với chất lượng tự động.',
        '6. Ghi trace từng stage, token counts/done_reason/model digest/config; chạy test lặp có chủ đích trên bộ phát triển mới để đo ổn định. Muốn kiểm chứng giả thuyết vẫn cần model mạnh hơn/dữ liệu thật sau khi sửa contract và code.', '',
        'Trong lượt debug này chỉ thêm công cụ/artefact chẩn đoán và test cho tính toàn vẹn của chẩn đoán. '
        'Chưa triển khai các sửa hành vi trên, nên không nhận là chất lượng MVP đã tăng. Kiểm thử kỹ thuật hiện 63 qua; '
        'điểm benchmark gốc B 0/20, C 1/20 và v3 0/6 vẫn giữ nguyên.', '',
        '## Nguồn và tái tạo', '',
        f'- [Offline, phân rã từng case]({refs}/offline.json), [guard probes]({refs}/boundary_probes.json), [scorer probes]({refs}/scoring_probes.json).',
        f'- [Request/response 6 experiment]({refs}/live/), [3 verifier probe]({refs}/verifier/), [runtime]({refs}/runtime.json), [audit JSON]({refs}/case_audit.json).',
        '- Source: [debugging.py](src/meeting_trace/evaluation/debugging.py), [debug_live.py](src/meeting_trace/evaluation/debug_live.py), [debug_verifier.py](src/meeting_trace/evaluation/debug_verifier.py).', '',
        '```bash', 'python src debug', 'python src debug-report', 'python src test', 'python src report --check', '```', '',
        'Các lệnh trên đọc dữ liệu đã lưu, không gọi model. debug-live/debug-verifier là lệnh gọi model đã claim; '
        'không chạy lại ngầm. Chẩn đoán dùng dữ liệu đã xem; không đưa kết quả này vào điểm holdout.', '']
    if len(live)!=6 or len(verifier)!=3: raise ValueError('Diagnostic live coverage incomplete')
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    (PATHS.root/'DEBUG.md').write_text(render(),encoding='utf-8',newline='\n')
    print('Generated DEBUG.md; no benchmark changes or inference.')


if __name__=='__main__': main()
