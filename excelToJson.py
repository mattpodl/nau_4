import json
import pandas

excel_data_df = pandas.read_excel('Dane_filmowe.xlsx', encode='utf-8', header=None, skiprows=1)

json_str = excel_data_df.to_json()

numrows = len(excel_data_df)  # 3 rows in your example
numcols = len(excel_data_df[0])
# for i in json_str:
#
dictionaryForJson = {}

for i in range(numrows):
    name = excel_data_df[0][i]
    dictionaryForJson[name] = {}
    print(name)
    for j in range(2, numcols):
        if j % 2:
            if excel_data_df[j][i] == excel_data_df[j][i]:
                dictionaryForJson[name][excel_data_df[j+1][i]] = int(excel_data_df[j][i])

print((dictionaryForJson))
gotowyJson = json.dumps(dictionaryForJson)
print('Excel Sheet to JSON:\n', gotowyJson)
# print(excel_data_df[1][0])
# print(excel_data_df)
# print(json.dumps(json_str, indent=1))
