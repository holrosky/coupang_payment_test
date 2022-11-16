import os
import sys
import datetime

from coupang_manager import CoupangManager
from excel_manager import ExcelManager
from ip_manager import IPManager
from collections import deque


class CoupangAutoTesting:
    def __init__(self):
        self.ip_manager = IPManager()
        self.excel_manager = ExcelManager()

        self.sheet_name = None
        self.select_sheet()

        self.coupang_manager = CoupangManager()

        self.current_acc_try_count = 0
        self.current_ip_try_count = 0
        self.current_mobile_try_count = 0

        self.acc_try_count = None
        self.acc_list = None
        self.ip_try_count = None
        self.mobile_try_count = None
        self.mobile_list = None
        self.test_range = None

        self.init_data()

    def select_sheet(self):
        sheet_name_list = self.excel_manager.get_sheets_name()
        sheet_name_list.remove('설정')

        print("테스팅 대상 시트 이름을 선택해 주세요.")

        for idx, name in enumerate(sheet_name_list):
            print('[' + str(idx+1) + '. ' + name + ']', end=' ')

        print('')

        while True:
            selected_num = input()

            if selected_num.isdigit() and len(sheet_name_list) >= int(selected_num) > 0:
                break

            else:
                print('올바른 번호를 입력해 주세요!')

        self.sheet_name = sheet_name_list[int(selected_num) - 1]
        self.excel_manager.set_sheet(self.sheet_name)

    def init_data(self):
        settings = self.excel_manager.get_setting()

        self.acc_try_count = settings['acc_try_count']
        self.acc_list = deque(settings['acc_list'])
        self.ip_try_count = settings['ip_try_count']
        self.mobile_try_count = settings['mobile_try_count']
        self.mobile_list = deque(settings['mobile_list'])
        self.test_range = settings['test_range']

    def run(self):
        if len(self.acc_list) < 1:
            print('쿠팡 아이디가 없습니다. 프로그램을 종료합니다.')
            return

        if len(self.mobile_list) < 1:
            print('휴대폰 정보가 없습니다. 프로그램을 종료합니다.')
            return

        if self.sheet_name not in self.test_range:
            print('테스트 범위가 주어지지 않았습니다. 프로그램을 종료합니다.')
            return

        else:
            try:
                current_acc_info = self.acc_list.popleft()
                self.acc_list.append(current_acc_info)

                current_mobile_info = self.mobile_list.popleft()
                self.mobile_list.append(current_mobile_info)

                self.ip_manager.change_ip()

                while self.coupang_manager.log_in(current_acc_info[0], current_acc_info[1]) == -1:
                    self.ip_manager.change_ip()

                for each_range in self.test_range[self.sheet_name]:
                    start, end = each_range
                    if start == 0:
                        start = 3

                        if end == 0:
                            end = self.excel_manager.get_num_of_test(self.sheet_name) + 2

                    for i in range(start, end + 1):
                        if self.current_ip_try_count >= self.ip_try_count:
                            print('설정한 IP 시도 횟수만큼 도달하여 IP를 변경합니다.')
                            self.coupang_manager.close()

                            self.ip_manager.change_ip()
                            while self.coupang_manager.log_in(current_acc_info[0], current_acc_info[1]) == -1:
                                self.ip_manager.change_ip()

                            self.current_ip_try_count = 0

                        if self.current_acc_try_count >= self.acc_try_count and len(self.acc_list) > 1:
                            print('설정한 쿠팡 계정 시도 횟수만큼 도달하여 쿠팡 계정을 변경합니다.')
                            self.coupang_manager.close()

                            current_acc_info = self.acc_list.popleft()
                            self.acc_list.append(current_acc_info)

                            while self.coupang_manager.log_in(current_acc_info[0], current_acc_info[1]) == -1:
                                self.ip_manager.change_ip()
                                self.current_ip_try_count = 0

                            self.current_acc_try_count = 0

                        if self.current_mobile_try_count >= self.mobile_try_count and len(self.mobile_list) > 1:
                            print('설정한 휴대폰 정보 시도 횟수만큼 도달하여 휴대폰 정보을 변경합니다.')
                            current_mobile_info = self.mobile_list.popleft()
                            self.mobile_list.append(current_mobile_info)

                            self.current_mobile_try_count = 0

                        print(i, '번째 행의 테스트 데이터를 가져옵니다...')
                        data = self.excel_manager.get_row_data(i)

                        if not data:
                            break

                        print(data)

                        if self.is_valid_data(data) and not self.is_already_tested(data) and not data[9]:
                            product_name, price, result = self.coupang_manager.test_product(data[4], current_mobile_info, int(data[8]), data[10])

                            self.current_acc_try_count += 1
                            self.current_ip_try_count += 1
                            self.current_mobile_try_count += 1

                            data[5] = current_mobile_info[1]

                            now = datetime.datetime.now()
                            data[6] = now.strftime('%Y-%m-%d %H:%M')
                            data[7] = self.ip_manager.get_ip()
                            data[11] = product_name
                            data[12] = price
                            data[13] = result

                            self.excel_manager.set_row_data(i, data)

                        else:
                            print(i, '번째 행의 테스트를 제외합니다.')

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                self.coupang_manager.close()
                self.ip_manager.disconnect()
                print(e, fname, exc_tb.tb_lineno)

    def is_already_tested(self, data):
        if not data[-1]:
            return False

        return True

    def is_valid_data(self, data):
        if not data[4]:
            return False

        if not data[8] or not data[8].isdigit():
            return False

        if ('다날' not in data) and ('모빌' not in data) and ('빌게이트' not in data):
            return False

        return True

    def disconnect_vpn(self):
        self.ip_manager.disconnect()

if __name__ == '__main__':
    coupang_auto_testing = CoupangAutoTesting()
    coupang_auto_testing.run()
    coupang_auto_testing.disconnect_vpn()
