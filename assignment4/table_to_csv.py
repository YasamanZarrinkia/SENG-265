# Implementation of table_to_csv without using any special library
# Not even re!!!!!!!!!!
import sys
import os.path
import fileinput

# GLOBAL VARIABLES TO INCREASE THE EFFICIENCY
data = ""  # Input data
MAX_COL = 0  # Maximum columns of the table


def row_data():  # Extracting Row data
    ans = ""
    global data
    global MAX_COL
    col_cnt = 0
    T_place = data.lower().find("<tr")  # Find the row tag
    T_end = data.find(">")
    table_finish = data.find("</table")
    if (
        T_place == -1 or T_end == -1 or T_place > table_finish
    ):  # check if there is any row in the current table
        return ""
    data = data[T_place + 1 :]
    T_end = data.find(">")
    data = data[T_end + 1 :]  # Ignore styling, etc ....
    column = column_data()
    while column != None:  # Adding column values to this row
        col_cnt += 1
        ans += column + ","
        column = column_data()
    ans = ans[:-1]  # Removing the extra ","
    if (
        MAX_COL < col_cnt
    ):  # Keeping track of the maximum number of columns of this table
        MAX_COL = col_cnt
    ans += "\n"
    return ans


def column_data():
    ans = ""
    global data
    T_place = data.lower().find("<td")  # Find the data tag
    H_place = data.lower().find("<th")  # Find the header tag
    T_end = data.find(">")
    row_finish = data.find("</tr")

    if (T_place != -1 and H_place == -1) or (
        T_place != -1 and H_place != -1 and T_place < H_place
    ):  # If the data is data tag (and not the header tag)
        if T_place == -1 or T_end == -1 or T_place > row_finish:
            return None
        data = data[T_place + 1 :]
        T_end = data.find(">")
        data = data[T_end + 1 :]  # Ignore styling, etc ....
        close_t = data.find("</td")
    else:  # If the data is header tag (and not the data tag)
        if H_place == -1 or T_end == -1 or H_place > row_finish:
            return None
        data = data[H_place + 1 :]
        T_end = data.find(">")
        data = data[T_end + 1 :]  # Ignore styling, etc ....
        close_t = data.find("</th")

    ans += data[:close_t]  # Capture the data between <td> and </td> (or <th> and </th>)
    data = data[close_t + 1 :]
    if ans.find(",") != -1:
        print(
            "Error: Invalid data. Comma character appeared in the data column: '%s'"
            % ans,
            file=sys.stderr,
        )
        sys.exit(8)
    ans = " ".join(ans.split())  # Remove extra Whitespaces
    return ans


def main():
    global data
    global MAX_COL

    input_file = fileinput.input()
    for line in input_file:
        data += line
    input_file.close()
    CSV = ""  # The CSV data
    CSVrow = ""  # The current CSV row beeing constructed from HTML
    table_count = 0  # Counter for the tables
    data = " ".join(data.split())  # Remove extra Whitespaces
    while data != "":
        T_place = data.lower().find("<table")  # Find the table tag
        T_end = data.find(">")
        if T_place == -1 or T_end == -1:
            break
        data = data[T_place + 1 :]
        T_end = data.find(">")
        data = data[T_end + 1 :]  # Ignore styling, etc ....
        table_count += 1
        CSV += (
            "TABLE " + str(table_count) + ":\n"
        )  # Add the table number to the CSV file
        MAX_COL = 0
        CSVrow = row_data()
        row_list = []
        while CSVrow != "":
            row_list.append(CSVrow)
            CSVrow = row_data()
        for row in row_list:
            cnt = row.count(",")
            if cnt < MAX_COL - 1:
                row = row[:-1]
                row += (MAX_COL - 1 - cnt) * ","
                row += "\n"
            CSV += row
        CSV += "\n"
    if (
        len(CSV) > 3 and CSV[-1] == "\n" and CSV[-2] == "\n"
    ):  # Removing extra new lines! Amazingly CSV.strip() does not work!!! (Tested on lab pc's)
        CSV = CSV[:-2]

    print(CSV)


if __name__ == "__main__":
    main()
