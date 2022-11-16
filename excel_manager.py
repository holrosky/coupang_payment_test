import json
import time

import gspread

class ExcelManager():
    def __init__(self):
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
        ]

        self.gc = gspread.service_account(filename='excel_credential.json', scopes= scope)

        with open("excel_credential.json", "r", encoding="UTF8") as st_json:
            json_data = json.load(st_json)


        self.doc = self.gc.open_by_url(json_data['excel_url'])
        self.sheet = None

    def get_setting(self):
        sheet = self.doc.worksheet('설정')

        setting_dict = {}

        setting_dict['acc_try_count'] = int(sheet.get('A1')[0][0])
        acc_id_list = sheet.col_values(2)[2:]
        acc_pwd_list = sheet.col_values(3)[2:]
        setting_dict['acc_list'] = []

        for id, pwd in zip(acc_id_list, acc_pwd_list):
            setting_dict['acc_list'].append((id, pwd))

        setting_dict['ip_try_count'] = int(sheet.get('E1')[0][0])
        setting_dict['mobile_try_count'] = int(sheet.get('G1')[0][0])

        mobile_carrier_list = sheet.col_values(7)[2:]
        mobile_number_list = sheet.col_values(8)[2:]
        dob_list = sheet.col_values(9)[2:]
        first_id_digit_list = sheet.col_values(10)[2:]

        setting_dict['mobile_list'] = []

        for mobile_carrier, mobile_number, dob, first_id_digit in zip(mobile_carrier_list, mobile_number_list, dob_list, first_id_digit_list):
            setting_dict['mobile_list'].append((mobile_carrier, mobile_number, dob, first_id_digit))

        setting_dict['test_range'] = {}

        test_sheet_name_list = sheet.col_values(11)[2:]
        test_range_start_list = sheet.col_values(12)[2:]
        test_range_end_list = sheet.col_values(13)[2:]

        for test_sheet_name, test_range_start, test_range_end in zip(test_sheet_name_list, test_range_start_list, test_range_end_list):
            if test_sheet_name not in setting_dict['test_range']:
                setting_dict['test_range'][test_sheet_name] = []

            setting_dict['test_range'][test_sheet_name].append((int(test_range_start), int(test_range_end)))

        return setting_dict

    def get_num_of_test(self, sheet_name):
        sheet = self.doc.worksheet(sheet_name)

        return len(sheet.col_values(11)[2:])

    def get_row_data(self, row_index):
        while True:
            try:
                row_data = self.sheet.get('A' + str(row_index) + ':N' + str(row_index))[0]

                while len(row_data) < 14:
                    row_data.append('')

                return row_data
            except Exception as e:
                print('구글 API 요청 시간이 너무 짧습니다. 1분 후 다시 시도합니다.')
                time.sleep(60)

    def set_row_data(self, row_index, data):
        while True:
            try:
                mobile_number = self.sheet.acell('F' + str(row_index))
                mobile_number.value = data[5]

                test_date = self.sheet.acell('G' + str(row_index))
                test_date.value = data[6]

                test_ip = self.sheet.acell('H' + str(row_index))
                test_ip.value = data[7]

                product_name = self.sheet.acell('L' + str(row_index))
                product_name.value = data[11]

                price = self.sheet.acell('M' + str(row_index))
                price.value = data[12]

                result = self.sheet.acell('N' + str(row_index))
                result.value = data[13]

                self.sheet.update_cells([mobile_number, test_date, test_ip, product_name, price, result])
                break
            except Exception as e:
                print('구글 API 요청 시간이 너무 짧습니다. 1분 후 다시 시도합니다.')
                time.sleep(60)

    def set_sheet(self, sheet_name):
        self.sheet = self.doc.worksheet(sheet_name)

    def get_sheets_name(self):
        return [s.title for s in self.doc.worksheets()]