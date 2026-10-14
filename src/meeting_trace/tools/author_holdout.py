"""Author six new synthetic cases before inference; never overwrite a suite.

Labels are authored by Codex with the author's authorization, not independently.
This module contains no model calls and is not a training-data generator.
"""
import hashlib
import json

from ..config import PATHS


def item(topic,type,contains,turn,status='confirmed',owner=None,due=None,conditions=None):
    return dict(topic=topic,type=type,contains=contains,status=status,owner=owner,due=due,
                conditions=conditions or [],evidence_turn='T'+str(turn))


CASES=[
dict(id='H01_reminders',title='Đổi kênh nhắc lịch sau khi kiểm tra chi phí',group='change',input_format='named',
raw='''Linh: Mình bàn nốt chuyện nhắc lịch cho tuần đầu mở thử nhé.
Dũng: Cho gửi SMS đi, khách không mở ứng dụng vẫn nhìn thấy.
Linh: Tạm chọn SMS, nhưng mình phải biết phí trước khi triển khai.
Hạnh: Nhà mạng tính cả những tin khách không nhận được do sai số điện thoại.
Quân: Với lượng lịch hiện tại thì khoản đó cao hơn dự toán khá nhiều.
Linh: Vậy SMS không còn phù hợp với tuần thử này rồi.
Dũng: Mình chuyển sang thông báo trong ứng dụng được không? Phần đó đã có sẵn.
Hạnh: Cách đó không phát sinh phí theo từng tin.
Quân: Nhưng chỉ gửi cho lịch đã xác nhận, lịch nháp thay đổi liên tục sẽ rất phiền.
Linh: Đúng, lịch nháp chưa phải lời hẹn với khách.
Hạnh: Thông báo hiện có đi qua hàng đợi, không hiện ngay lập tức.
Quân: Trễ vài phút thì vẫn dùng được, mình nhắc trước buổi hẹn khá lâu.
Dũng: Khách tắt thông báo thì mình có tự gửi SMS thay thế không?
Hạnh: Đợt này chưa có phần chuyển kênh như vậy.
Linh: Chốt dùng thông báo trong ứng dụng, chỉ cho lịch đã xác nhận. SMS không dùng ở tuần thử này.
Dũng: Như vậy khách tắt thông báo thì chưa có kênh thay thế ở phiên bản này.
Quân: Em sẽ giải thích giới hạn đó khi được hỏi, không hứa có SMS dự phòng.
Linh: Ừ, phần kênh nhắc lịch dừng ở kết luận vừa rồi.''',
items=[item('nhắc lịch','decision','thông báo trong ứng dụng',15,conditions=['chỉ cho lịch đã xác nhận'])],
history=[2,7,15],intermediate=[2],lesson='Giữ kênh cuối và phạm vi lịch đã xác nhận; không tự tạo cơ chế SMS dự phòng.'),
dict(id='H02_conditional_export',title='Giao việc bằng tên trong transcript không có người nói',group='clear',input_format='plain',
raw='''Danh sách khách của đợt thử cần gửi cho đối tác để họ kiểm tra số liệu.
Họ đã có màn hình xem tổng số, nhưng không có danh sách từng dòng.
File gửi ra vẫn dùng các cột đã được duyệt ở lần làm trước.
Phản hồi của đối tác là họ cần CSV đã mã hóa, không nhận file mở trực tiếp.
Mình không bổ sung số điện thoại hoặc địa chỉ vào file lần này.
Vướng mắc là pháp chế chưa xác nhận quyền xuất bản danh sách.
Hồ sơ đã được gửi đi, nhưng chưa có câu trả lời về phạm vi được chia sẻ.
Vậy hiện chưa ai nên tạo file rồi gửi ra ngoài.
Ngọc có tài khoản xuất dữ liệu, đúng không?
Có, Ngọc đã dùng tài khoản đó để làm bản thử nội bộ.
Tài khoản dùng được không thay cho việc pháp chế đồng ý.
Đúng, đây là hai điều kiện khác nhau.
Nếu pháp chế không xác nhận thì mình dừng việc gửi, không tìm tài khoản khác để làm.
Ngọc xuất bản CSV đã mã hóa sau khi pháp chế xác nhận, hạn trước thứ Năm.
Ngọc đã biết việc này; khi có xác nhận thì bạn ấy mới thực hiện.
Trước lúc đó, quyền xuất vẫn giữ như cũ nhưng chưa được dùng cho đối tác.
Nếu trả lời của pháp chế đến muộn, hạn giao cũng cần được trao đổi lại.
Mình kết thúc phần danh sách ở điều kiện và hạn vừa nêu.''',
items=[item('xuất dữ liệu','request_feedback','CSV đã mã hóa',4,'needs_confirmation'),
       item('pháp chế','issue','chưa xác nhận',6,'needs_confirmation'),
       item('xuất dữ liệu','action','CSV đã mã hóa',14,'needs_confirmation','Ngọc','thứ Năm',['sau khi pháp chế xác nhận'])],
history=[],intermediate=[],lesson='Tên người nhận đến từ nội dung giao việc; cam kết phụ thuộc pháp chế chưa thể coi là công việc vô điều kiện.'),
dict(id='H03_reopened_backup',title='Quyết định sao lưu được mở lại vì dung lượng',group='unresolved',input_format='labels',
raw='''Người nói 1: Thời gian giữ bản sao lưu hiện cần được thống nhất lại.
Người nói 2: Bảy ngày thì hơi ngắn nếu cuối tháng mới phát hiện lỗi dữ liệu.
Người nói 1: Vậy chốt giữ ba mươi ngày để đủ thời gian đối chiếu.
Người nói 3: Em hỏi lại phần dung lượng, mình đã tính cả bản sao hằng ngày chưa?
Người nói 2: Con số hôm qua mới tính dữ liệu gốc.
Người nói 3: Bản sao đầy đủ khá lớn, không phải ngày nào cũng chỉ lưu phần thay đổi.
Người nói 1: Anh nghĩ phần còn trống đủ, nhưng chưa có bảng tính chi tiết.
Người nói 2: Mình có thể giảm xuống mười bốn ngày nếu ba mươi ngày không đủ.
Người nói 3: Em đang nhìn giới hạn gói hiện tại, nó không tự tăng dung lượng.
Người nói 2: Mua thêm lúc này có vượt dự toán không?
Người nói 3: Vướng mắc là chưa có số liệu dung lượng của bản sao hằng ngày.
Người nói 1: Như vậy câu chốt ba mươi ngày lúc đầu chưa có cơ sở đủ chắc.
Người nói 1: Hủy kết luận ba mươi ngày, mình mở lại phần này.
Người nói 2: Mười bốn ngày cũng mới là phương án để cân nhắc thôi.
Người nói 3: Khi có dung lượng thực tế thì mới biết phương án nào dùng được.
Người nói 1: Hôm nay chưa chốt số ngày giữ bản sao, cả bảy, mười bốn và ba mươi ngày đều chưa được chọn.
Người nói 2: Em ghi lại để người đọc không hiểu ba mươi ngày còn hiệu lực.
Người nói 3: Ừ, lần tới mình quay lại với số liệu thực tế.''',
items=[item('sao lưu','unresolved','chưa chốt số ngày giữ bản sao',16,'unresolved'),
       item('dung lượng','issue','chưa có số liệu dung lượng',11,'needs_confirmation')],
history=[3,8,13,16],intermediate=[3,8],lesson='Không giữ quyết định đã hủy; một phương án thay thế được nhắc đến chưa trở thành lựa chọn cuối.'),
dict(id='H04_discount_request',title='Phản hồi kinh doanh và lời nhận việc có điều kiện',group='indirect',input_format='mixed',
raw='''Lan: Phần hạn mức giảm giá có phản hồi từ nhóm kinh doanh.
Lan: Họ muốn tăng hạn mức giảm giá lên 20% cho đợt giới thiệu.
Nhóm tài chính đã xem đề xuất này chưa?
Lan: Chưa, họ mới nhận bảng dự toán sáng nay.
Huy: Mức đang chạy là 10%, mình chưa đổi cấu hình nào.
Nếu lên 20% thì có áp dụng cho mọi khách hàng không?
Lan: Câu hỏi đó cũng chưa được trả lời, bên kinh doanh mới nêu mức mong muốn.
Huy: Em không muốn cập nhật bảng rồi sau đó phải thu lại vì chưa được duyệt.
Vậy hôm nay mình ghi phản hồi, còn số mới cần chờ tài chính.
Lan: Đúng, chưa chốt tăng hạn mức giảm giá trong buổi này.
Huy: Nếu tài chính xác nhận, em nhận cập nhật bảng hạn mức giảm giá trước thứ Hai.
Chưa có xác nhận thì phần bảng vẫn để như đang dùng nhé.
Huy: Ừ, lời nhận việc của em chỉ có hiệu lực sau xác nhận đó.
Lan: Nếu tài chính không đồng ý thì không cập nhật theo đề xuất 20%.
Mình có cần hứa với kinh doanh về ngày áp dụng chưa?
Lan: Chưa hứa, vì thời điểm xác nhận còn chưa biết.
Huy: Phần hạn mức và điều kiện cập nhật đã rõ như vậy.
Lan: Em dừng phần trao đổi này ở phản hồi và câu chưa chốt.''',
items=[item('hạn mức giảm giá','request_feedback','20%',2,'needs_confirmation'),
       item('hạn mức giảm giá','unresolved','chưa chốt tăng hạn mức giảm giá',10,'unresolved'),
       item('hạn mức giảm giá','action','cập nhật bảng hạn mức giảm giá',11,'needs_confirmation','Huy','thứ Hai',['Nếu tài chính xác nhận'])],
history=[2,10],intermediate=[2],lesson='Yêu cầu của kinh doanh chưa là quyết định; việc được nhận có điều kiện phải giữ điều kiện và chưa tự chuyển thành vô điều kiện.'),
dict(id='H05_webhook_limit',title='Chốt giới hạn webhook và người gửi báo cáo',group='clear',input_format='named',
raw='''Quân: Webhook thất bại ở phía nhận thì mình cần thống nhất cách gửi lại.
Mai: Có thể gửi lại liên tục cho đến khi nhận được phản hồi thành công.
Dũng: Nếu phía nhận ngừng hoạt động cả ngày thì hàng đợi sẽ phình rất lớn.
Quân: Đúng, mình phải có giới hạn để không chặn các thông báo sau.
Linh: Phía đối tác thường khôi phục trong vài phút, nhưng không bảo đảm luôn như vậy.
Mai: Vậy gửi lại tối đa ba lần, cách nhau 30 giây được không?
Dũng: Sau lần thứ ba vẫn lỗi thì ghi trạng thái thất bại cho người vận hành xem.
Quân: Không tự coi thất bại là thành công để bỏ qua nhé.
Linh: Trạng thái đó cần nhìn được trong màn hình theo dõi hiện có.
Mai: Màn hình đã có chỗ hiển thị lỗi, không cần tạo một màn hình mới cho lần này.
Dũng: Khoảng 30 giây có đủ cho đối tác đáp lại không?
Linh: Với thời gian phản hồi đã đo thì đủ để thử cách này.
Quân: Chốt gửi lại tối đa ba lần, cách nhau 30 giây; sau đó vẫn lỗi thì giữ trạng thái thất bại.
Quân: Mai gửi báo cáo kiểm tra webhook cho nhóm sau khi thử cấu hình này nhé.
Mai: Em sẽ gửi báo cáo kiểm tra webhook trước thứ Sáu.
Dũng: Trong báo cáo nhớ giữ cả trường hợp đối tác không hoạt động.
Mai: Em hiểu phạm vi kiểm tra, không chỉ gửi trường hợp thành công.
Quân: Mình kết thúc ở giới hạn gửi lại và việc gửi báo cáo đã thống nhất.''',
items=[item('webhook','decision','gửi lại',13,conditions=['tối đa ba lần','cách nhau 30 giây','trạng thái thất bại']),
       item('kiểm tra webhook','action','báo cáo kiểm tra webhook',15,'confirmed','Mai','thứ Sáu')],
history=[2,6,13],intermediate=[2],lesson='Giữ giới hạn số lần/khoảng cách và trạng thái sau thất bại; giao và nhận cùng một báo cáo là một công việc.'),
dict(id='H06_unsettled_rota',title='Ok và để em xem chưa tạo người phụ trách lịch trực',group='indirect',input_format='plain',
raw='''Lịch trực hỗ trợ trong đợt mở thử vẫn còn hai cách xếp.
Mình có thể xếp hai người luân phiên để mỗi người có thời gian làm việc khác.
Nếu chỉ có hai người thì hôm một người nghỉ sẽ khó thay thế.
Đúng, nhưng đợt thử cũng chưa có nhiều yêu cầu hỗ trợ.
Có cần ba người cùng chia ca ngay từ đầu không?
Có thể, nhưng phải xem nhóm hỗ trợ có người trống lịch không đã.
Phương án ba người chia ca cũng đáng cân nhắc, chưa biết có đủ người không.
Để em xem lịch bên đó.
Ok với việc hỏi trước, chưa nên gửi lịch cho khách lúc này.
Vướng mắc là chưa có lịch làm việc của nhóm hỗ trợ để kiểm tra ca trùng.
Em nói xem lịch thôi, chưa nhận việc chốt danh sách trực.
Ừ, mình cũng chưa giao ai trách nhiệm chốt danh sách trong buổi này.
Nếu hỏi được thì lần tới sẽ có cơ sở để chọn hai hay ba người.
Khách có đang chờ một ngày chính thức mở hỗ trợ chưa?
Họ mới hỏi khoảng thời gian dự kiến, chưa yêu cầu lịch từng ca.
Vậy đừng tự ghi tên người trực khi chưa biết người nào tham gia được.
Hôm nay chưa thống nhất lịch trực; chưa giao ai chốt danh sách.
Mình giữ hai phương án và câu hỏi về lịch làm việc cho buổi sau.''',
items=[item('lịch trực','unresolved','chưa thống nhất lịch trực',17,'unresolved'),
       item('lịch làm việc','issue','chưa có lịch làm việc',10,'needs_confirmation')],
history=[2,7,17],intermediate=[2,7],lesson='Không biến ok/để em xem thành một công việc đã giao; giữ thiếu danh tính thay vì tạo người phụ trách.')]


def main():
    manifest_path=PATHS.root/'data/holdout-v3/manifest.json'
    if manifest_path.exists(): raise ValueError('Suite đã có; không ghi đè dữ liệu hoặc kỳ vọng.')
    manifest=[]
    for case in CASES:
        transcript='data/holdout-v3/'+case['id']+'.txt'
        expected='tests/fixtures/holdout-v3/'+case['id']+'.expected.json'
        raw=case['raw']+'\n'
        path=PATHS.root/transcript
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x',encoding='utf-8',newline='\n') as handle: handle.write(raw)
        gold={k:case[k] for k in ['id','title','group','input_format','items','lesson']}
        gold.update(split='fresh_holdout',dataset_version='3.0',
            history_turns=['T'+str(t) for t in case['history']],
            intermediate_turns=['T'+str(t) for t in case['intermediate']],
            transcript_sha256=hashlib.sha256(raw.encode()).hexdigest(),
            authored_before_inference=True,labeler='Codex/AI hỗ trợ tác giả, không độc lập')
        fixture=PATHS.root/expected
        fixture.parent.mkdir(parents=True,exist_ok=True)
        with fixture.open('x',encoding='utf-8',newline='\n') as handle:
            handle.write(json.dumps(gold,ensure_ascii=False,indent=2)+'\n')
        manifest.append({**{key:gold[key] for key in ['id','title','group','input_format','dataset_version','transcript_sha256']},
            'transcript':transcript,'expected':expected,'expected_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest()})
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Authored six cases and labels before inference. No model calls.')


if __name__=='__main__': main()
