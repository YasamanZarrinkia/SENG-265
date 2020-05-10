#!/usr/bin/env python3

import argparse
import os
import sys
import csv


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# Check if a str type object is numeric or not
def isnum(val):
    try:
        float(val)
    except ValueError:
        return False
    return True


def check_valid(data, parser):  # Error Checking
    header = [x.lower() for x in data[0]]
    args = vars(parser.parse_args())

    if args["groupby"] not in header:
        print(
            "Error: %s: no field with name %s found"
            % (args["input"][0], args["groupby"][0]),
            file=sys.stderr,
        )
        sys.exit(8)

    if args["min"] is not None:
        for i in args["min"]:
            for m in i:
                if m not in header:
                    print(
                        "Error: %s: no min argument with name %s found"
                        % (args["input"][0], m),
                        file=sys.stderr,
                    )
                    sys.exit(9)

    if args["max"] is not None:
        for i in args["max"]:
            for m in i:
                if m not in header:
                    print(
                        "Error: %s: no max argument with name %s found"
                        % (args["input"][0], m),
                        file=sys.stderr,
                    )
                    sys.exit(9)

    if args["mean"] is not None:
        for i in args["mean"]:
            for m in i:
                if m not in header:
                    print(
                        "Error: %s: no mean argument with name %s found"
                        % (args["input"][0], m),
                        file=sys.stderr,
                    )
                    sys.exit(9)

    if args["sum"] is not None:
        for i in args["sum"]:
            for m in i:
                if m not in header:
                    print(
                        "Error: %s: no sum with name %s found" % (args["input"][0], m),
                        file=sys.stderr,
                    )
                    sys.exit(9)

    if args["top"] is not None:
        for m in args["top"]:
            if m[1] not in header:
                print(
                    "Error: %s: no top argument with name %s found"
                    % (args["input"][0], m[1]),
                    file=sys.stderr,
                )
                sys.exit(9)


def main():
    # Parse the command line input
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs=1)
    parser.add_argument("--top", nargs=2, action="append", type=str.lower)
    parser.add_argument("--mean", nargs="*", action="append", type=str.lower)
    parser.add_argument("--max", nargs="*", action="append", type=str.lower)
    parser.add_argument("--min", nargs="*", action="append", type=str.lower)
    parser.add_argument("--sum", nargs="*", action="append", type=str.lower)
    parser.add_argument("--count", nargs="?", type=str.lower)
    parser.add_argument("--groupby", type=str.lower)

    args = vars(parser.parse_args())
    data_raw = read_file(args["input"][0])  # Read Input file
    data_raw[0] = [x.lower() for x in data_raw[0]]
    check_valid(data_raw, parser)
    groupby_arg = args["groupby"]
    grouped_data = group_by(data_raw, groupby_arg, args)
    print_output(grouped_data, groupby_arg)


def print_output(d, groupby_arg):  # Print output
    # init empty array (1 + unique values) by (1 + number of tasks)
    tasks = list(d.keys())
    unique_values = list(d[tasks[0]].keys())
    final_output = [
        [None for i in range(len(tasks) + 1)] for j in range(1 + len(unique_values))
    ]

    final_output[0][0] = groupby_arg
    for i in range(0, len(tasks)):
        final_output[0][i + 1] = tasks[i]

    for j in range(0, len(unique_values)):
        final_output[j + 1][0] = unique_values[j]
        for i in range(0, len(tasks)):
            final_output[j + 1][i + 1] = d[tasks[i]][unique_values[j]]

    print(final_output)

    # Save to file
    writer = csv.writer(open("output.csv", "w"), delimiter=",", lineterminator="\n")
    for i in final_output:
        writer.writerow(i)


# Group By Function
def group_by(data, groupby_arg, args):
    # creates a dictionary from functions to column header values
    tasks = {}
    for key, value in args.items():
        if key is "input" or key is "groupby":
            continue
        if value is not None:
            for j in value:
                if key in tasks:
                    for i in j:
                        tasks[key].append(i)
                else:
                    tasks[key] = []
                    for i in j:
                        tasks[key].append(i)

    grouped_data = {}
    for key, value in tasks.items():
        for item in value:
            if key == "count":
                result_out, capped = find_count(data, groupby_arg, grouped_data, args)
                if capped:
                    grouped_data[key + "_capped"] = result_out
                else:
                    grouped_data[key] = result_out

            if key == "min":
                result_out, capped = find_min(
                    data, groupby_arg, item, grouped_data, args
                )
                if capped:
                    grouped_data[key + "_" + item + "_capped"] = result_out
                else:
                    grouped_data[key + "_" + item] = result_out

            if key == "max":
                result_out, capped = find_max(
                    data, groupby_arg, item, grouped_data, args
                )
                if capped:
                    grouped_data[key + "_" + item + "_capped"] = result_out
                else:
                    grouped_data[key + "_" + item] = result_out

            if key == "mean":
                result_out, capped = find_mean(
                    data, groupby_arg, item, grouped_data, args
                )
                if capped:
                    grouped_data[key + "_" + item + "_capped"] = result_out
                else:
                    grouped_data[key + "_" + item] = result_out
            if key == "sum":
                result_out, ignore_value, capped = find_sum(
                    data, groupby_arg, item, grouped_data, args
                )
                if capped:
                    grouped_data[key + "_" + item + "_capped"] = result_out
                else:
                    grouped_data[key + "_" + item] = result_out
        if key == "top":
            result_out, capped = find_top(
                data, groupby_arg, item, grouped_data, args, int(args["top"][0][0])
            )
            if capped:
                grouped_data[
                    key + str(args["top"][0][0]) + "_" + item + "_capped"
                ] = result_out
            else:
                grouped_data[key + str(args["top"][0][0]) + "_" + item] = result_out
    return grouped_data


# Top-k Function
def find_top(data, groupby_arg, field_name, grouped_data, args, k):
    result = {}
    print(k)
    groupby_index = data[0].index(groupby_arg)
    field_name_index = data[0].index(field_name)
    # start from 1 to ignore the header
    freqs = {}

    counter = 0
    non_numberic_count = 0
    capped = False
    for row_index in range(1, len(data)):
        if non_numberic_count > 100:
            print(
                "Error: %s: more than 100 non-numeric values found in aggregate column '%s'"
                % (args["input"][0], groupby_arg),
                file=sys.stderr,
            )
            sys.exit(7)
        if counter > 1000:
            print(
                "Error: %s: %s has been capped at 1000 values"
                % (args["input"][0], groupby_arg),
                file=sys.stderr,
            )
            capped = True

        if data[row_index][groupby_index] in freqs:
            freqs[data[row_index][groupby_index]].append(
                data[row_index][field_name_index]
            )
        else:
            counter += 1
            freqs[data[row_index][groupby_index]] = [data[row_index][field_name_index]]

    for key, value in freqs.items():
        temp_dict = {}
        for z in freqs[key]:
            if z in temp_dict:
                temp_dict[z] += 1
            else:
                temp_dict[z] = 1
        k_counter = 0
        if len(list(temp_dict.keys())) > 20:
            print(
                "Error: %s: %s has been capped at 20 distinct values"
                % (args["input"][0], key),
                file=sys.stderr,
            )
            capped = True
        sorted(temp_dict.items(), key=lambda x: x[1], reverse=True)
        for key_t, value_t in temp_dict.items():
            if k_counter == k:
                # just to trim the last two characters
                result[key] = result[key][:-2]
                break
            else:
                k_counter += 1
                if key in result:
                    result[key] += str(key_t) + ": " + str(temp_dict[key_t]) + ", "
                else:
                    result[key] = str(key_t) + ": " + str(temp_dict[key_t]) + ", "

    return result, capped


# Count Function
def find_count(data, groupby_arg, grouped_data, args):
    result = {}
    groupby_index = data[0].index(groupby_arg)
    # start from 1 to ignore the header
    counter = 0
    capped = False
    for row_index in range(1, len(data)):
        if counter > 1000:
            print(
                "Error: %s: %s has been capped at 1000 values"
                % (args["input"][0], groupby_arg),
                file=sys.stderr,
            )
            capped = True
        if data[row_index][groupby_index] in result:
            result[data[row_index][groupby_index]] += 1
        else:
            counter += 1
            result[data[row_index][groupby_index]] = 1

    return result, capped


# Min/Max Functions
def find_min(data, groupby_arg, field_name, grouped_data, args):
    result = {}
    groupby_index = data[0].index(groupby_arg)
    field_name_index = data[0].index(field_name)
    # start from 1 to ignore the header

    counter = 0
    non_numberic_count = 0
    capped = False
    for row_index in range(1, len(data)):
        if non_numberic_count > 100:
            print(
                "Error: %s: more than 100 non-numeric values found in aggregate column '%s'"
                % (args["input"][0], groupby_arg),
                file=sys.stderr,
            )
            sys.exit(7)
        if counter > 1000:
            print(
                "Error: %s: %s has been capped at 1000 values"
                % (args["input"][0], groupby_arg),
                file=sys.stderr,
            )
            capped = True
        if data[row_index][groupby_index] in result:
            if not isnum(data[row_index][field_name_index]):
                print(
                    "Error: %s: %s: can’t compute %s on non-numeric value '%s'"
                    % (
                        args["input"][0],
                        str(counter + 1),
                        groupby_arg,
                        str(data[row_index][field_name_index]),
                    ),
                    file=sys.stderr,
                )
                non_numberic_count += 1
                continue
            if float(result[data[row_index][groupby_index]]) > float(
                data[row_index][field_name_index]
            ):
                result[data[row_index][groupby_index]] = float(
                    data[row_index][field_name_index]
                )
        else:
            counter += 1
            if not isnum(data[row_index][field_name_index]):
                print(
                    "Error: %s: %s: can’t compute %s on non-numeric value '%s'"
                    % (
                        args["input"][0],
                        str(counter + 1),
                        groupby_arg,
                        str(data[row_index][field_name_index]),
                    ),
                    file=sys.stderr,
                )
                non_numberic_count += 1
                continue
            else:
                result[data[row_index][groupby_index]] = float(
                    data[row_index][field_name_index]
                )

    return result, capped


def find_max(data, groupby_arg, field_name, grouped_data, args):
    result = {}
    groupby_index = data[0].index(groupby_arg)
    field_name_index = data[0].index(field_name)
    # start from 1 to ignore the header

    counter = 0
    non_numberic_count = 0
    capped = False
    for row_index in range(1, len(data)):
        if non_numberic_count > 100:
            print(
                "Error: %s: more than 100 non-numeric values found in aggregate column '%s'"
                % (args["input"][0], groupby_arg),
                file=sys.stderr,
            )
            sys.exit(7)
        if counter > 1000:
            print(
                "Error: %s: %s has been capped at 1000 values"
                % (args["input"][0], groupby_arg),
                file=sys.stderr,
            )
            capped = True
        if data[row_index][groupby_index] in result:
            if not isnum(data[row_index][field_name_index]):
                print(
                    "Error: %s: %s: can’t compute %s on non-numeric value '%s'"
                    % (
                        args["input"][0],
                        str(counter + 1),
                        groupby_arg,
                        str(data[row_index][field_name_index]),
                    ),
                    file=sys.stderr,
                )
                non_numberic_count += 1
                continue
            if float(result[data[row_index][groupby_index]]) < float(
                data[row_index][field_name_index]
            ):
                result[data[row_index][groupby_index]] = float(
                    data[row_index][field_name_index]
                )
        else:
            counter += 1
            if not isnum(data[row_index][field_name_index]):
                print(
                    "Error: %s: %s: can’t compute %s on non-numeric value '%s'"
                    % (
                        args["input"][0],
                        str(counter + 1),
                        groupby_arg,
                        str(data[row_index][field_name_index]),
                    ),
                    file=sys.stderr,
                )
                non_numberic_count += 1
                continue
            else:
                result[data[row_index][groupby_index]] = float(
                    data[row_index][field_name_index]
                )

    return result, capped


# Mean Function
def find_mean(data, groupby_arg, field_name, grouped_data, args):
    summed_dict, counts, capped = find_sum(
        data, groupby_arg, field_name, grouped_data, args
    )
    result = {}
    for key, value in counts.items():
        result[key] = float(summed_dict[key]) / value

    return result, capped


# Sum Function
def find_sum(data, groupby_arg, field_name, grouped_data, args):
    result = {}
    counts = {}  # this is just to be used in find_mean
    groupby_index = data[0].index(groupby_arg)
    field_name_index = data[0].index(field_name)
    # start from 1 to ignore the header

    counter = 0
    non_numberic_count = 0
    capped = False
    for row_index in range(1, len(data)):
        if non_numberic_count > 100:
            print(
                "Error: %s: more than 100 non-numeric values found in aggregate column '%s'"
                % (args["input"][0], groupby_arg),
                file=sys.stderr,
            )
            sys.exit(7)
        if counter > 1000:
            print(
                "Error: %s: %s has been capped at 1000 values"
                % (args["input"][0], groupby_arg),
                file=sys.stderr,
            )
            capped = True
        if data[row_index][groupby_index] in result:
            if not isnum(data[row_index][field_name_index]):
                print(
                    "Error: %s: %s: can’t compute %s on non-numeric value '%s'"
                    % (
                        args["input"][0],
                        str(counter + 1),
                        groupby_arg,
                        str(data[row_index][field_name_index]),
                    ),
                    file=sys.stderr,
                )
                non_numberic_count += 1
                continue
            counts[data[row_index][groupby_index]] += 1
            result[data[row_index][groupby_index]] += float(
                data[row_index][field_name_index]
            )
        else:
            counter += 1
            counts[data[row_index][groupby_index]] = 1
            if not isnum(data[row_index][field_name_index]):
                print(
                    "Error: %s: %s: can’t compute %s on non-numeric value '%s'"
                    % (
                        args["input"][0],
                        str(counter + 1),
                        groupby_arg,
                        str(data[row_index][field_name_index]),
                    ),
                    file=sys.stderr,
                )
                non_numberic_count += 1
                continue
            else:
                result[data[row_index][groupby_index]] = float(
                    data[row_index][field_name_index]
                )

    return result, counts, capped


def read_file(path):
    try:
        with open(path, encoding="utf-8-sig") as csv_file:
            csv_read = csv.reader(csv_file, delimiter=",")
            data = [row for row in csv_read]
    except:
        print("Error: %s: Cannot open the file!" % path[0], file=sys.stderr)
        sys.exit(6)

    return data


if __name__ == "__main__":
    main()
