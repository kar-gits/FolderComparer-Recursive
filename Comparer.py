import os
import filecmp

from Singleton import Singleton
import Utils


class Comparer(Singleton):
    def compare(self, source, destination, module):
        report = self.recursive_dircmp(source, destination)
        if report["left"]:
            items = []
            for item in report["left"]:
                item = item[1:]
                path = Utils.join_path(source, item)
                if os.path.isdir(path):
                    data = self.list_dirs_files(path)
                    items.extend(data)
            report["left"].extend(i[len(source):] for i in items)

        if report["right"]:
            items = []
            for item in report["right"]:
                item = item[1:]
                path = Utils.join_path(destination, item)
                if os.path.isdir(path):
                    data = self.list_dirs_files(path)
                    items.extend(data)
            report["right"].extend(i[len(destination):] for i in items)
        records = []
        files = []
        directories = []
        not_identical = []
        left_files, right_files, common_files = 0, 0, 0
        left_directories, right_directories, common_directories = 0, 0, 0
        left_not_identical, right_not_identical, common_not_identical = 0, 0, 0

        if report["left"]:
            for item in report["left"]:
                item = item[1:]
                s_path = Utils.join_path(source, item)
                record = {"Name": item.split('/')[-1], "Indicator": "<=", "Compare": "Source", "SPath": s_path,
                          "DPath": ""}
                if os.path.isfile(s_path):
                    _, ext = os.path.splitext(item)
                    record["FileType"] = "File"
                    record["Extension"] = ext
                    record["SSize"] = os.stat(record["SPath"]).st_size
                    record["DSize"] = 0
                    left_files += 1
                    record["Result"] = "Identical" if record["SSize"] == record["DSize"] else "Not Identical"
                else:
                    record["FileType"] = "Directory"
                    record["Result"] = "Not Identical"
                    left_directories += 1
                if record['Result'] == 'Not Identical' and record["FileType"] == "File":
                    left_not_identical += 1
                records.append(record)

        if report["right"]:
            for item in report["right"]:
                item = item[1:]
                d_path = Utils.join_path(destination, item)
                record = {"Name": item.split('/')[-1], "Indicator": "=>", "Compare": "Destination", "SPath": "",
                          "DPath": d_path}
                if os.path.isfile(d_path):
                    _, ext = os.path.splitext(item)
                    record["FileType"] = "File"
                    record["Extension"] = ext
                    record["DSize"] = os.stat(record["DPath"]).st_size
                    record["SSize"] = 0
                    right_files += 1
                    record["Result"] = "Identical" if record["SSize"] == record["DSize"] else "Not Identical"
                else:
                    record["FileType"] = "Directory"
                    record["Result"] = "Not Identical"
                    right_directories += 1
                if record['Result'] == 'Not Identical' and record["FileType"] == "File":
                    right_not_identical += 1
                records.append(record)

        if report["both"]:
            for item in report["both"]:
                item = item[1:]
                s_path = Utils.join_path(source, item)
                d_path = Utils.join_path(destination, item)
                record = {"Name": item.split('/')[-1], "Indicator": "==", "Compare": "Both", "SPath": s_path,
                          "DPath": d_path}
                if os.path.isfile(s_path) and os.path.isfile(d_path):
                    _, ext = os.path.splitext(item)
                    record["FileType"] = "File"
                    record["Extension"] = ext
                    record["SSize"] = os.stat(record["SPath"]).st_size
                    record["DSize"] = os.stat(record["DPath"]).st_size
                    common_files += 1
                    record["Result"] = "Identical" if record["SSize"] == record["DSize"] else "Not Identical"
                else:
                    record["FileType"] = "Directory"
                    record["Result"] = "Identical"
                    common_directories += 1
                if record['Result'] == 'Not Identical' and record["FileType"] == "File":
                    common_not_identical += 1
                records.append(record)

        files.extend((left_files, right_files, common_files))
        directories.extend((left_directories, right_directories, common_directories))
        not_identical.extend((left_not_identical, right_not_identical, common_not_identical))

        self.overview(source, destination, files, directories, not_identical, module)
        return records

    @staticmethod
    def list_dirs_files(folder):
        dirs_files = []
        for root, directories, files in os.walk(folder):
            for directory in directories:
                dirs_files.append(Utils.join_path(root, directory))
            for file in files:
                dirs_files.append(Utils.join_path(root, file))
        return dirs_files

    def recursive_dircmp(self, source, destination, prefix=''):
        comparison = filecmp.dircmp(source, destination)
        data = {
                'left': [r'{}/{}'.format(prefix, i) for i in comparison.left_only],
                'right': [r'{}/{}'.format(prefix, i) for i in comparison.right_only],
                'both': [r'{}/{}'.format(prefix, i) for i in comparison.common],
        }
        if comparison.common_dirs:
            for folder in comparison.common_dirs:
                # Compare common folder and add results to the report
                sub_source = Utils.join_path(source, folder)
                sub_destination = Utils.join_path(destination, folder)
                sub_report = self.recursive_dircmp(sub_source, sub_destination, (prefix + "/" + folder))
                # Add results from sub_report to main report
                for key, value in sub_report.items():
                    data[key] += value
        return data

    @staticmethod
    def overview(source, destination, files, directories, not_identical, module):
        print('\nCOMPARISON OF FILES BETWEEN FOLDERS:\n')
        print('\tFOLDER 1: {}'.format(source))
        print('\tFOLDER 2: {}\n'.format(destination))
        print('\tModule Name: {}\n'.format(module))

        width = 15
        col_list = ['PARTICULARS', 'DIRECTORIES', 'FILES', 'NOT IDENTICAL', 'REMARKS']
        col_format = '\t{:<15}{:<15}{:<10}{:<17}{:<10}'.format(*col_list)
        f_line = '-'*width*len(col_list)
        t_line = '='*width*len(col_list)

        print(f_line + '\n' + col_format + '\n' + f_line)
        row_list = ['Source', 'Destination', 'BOTH']
        directories.append(sum(directories))
        files.append(sum(files))
        remarks = ['left', 'left', '-']
        data = zip(row_list, directories, files, not_identical, remarks)
        for row in data:
            if row[0] == 'BOTH':
                print(t_line)
            print('\t{:<15}{:<15}{:<10}{:<17}{:<10}'.format(*row))
