import os
import json
from collections import defaultdict
from reportlab.pdfgen import canvas
import numpy as np

global entire_dict


'''
'''
class SearchInformation:
    def __init__(self):
        self.current_path()

    def current_path(self):
        nearest_dirs = self.nearest_directories()
        self.search_directory(os.getcwd(), nearest_dirs)

    def nearest_directories(self):
        files = [f for f in os.listdir('.') if os.path.isdir(f)]
        return self.validate_dirs(files)

    def validate_dirs(self, files):
        dirs = []
        [dirs.append(f) for f in files if not f.startswith('.')]
        return dirs

    def search_directory(self, *args):
        ''' Searches for the directory in the root list '''
        path, uppers_funnels = args
        root_list = []
        for root, dirs, files in os.walk(path):
            root_list.append(root)

        self.find_files(root_list, uppers_funnels)

    def find_files(self, root_directory, upp_funnel):
        ''' Looks for the approrpiate file '''

        total_list = []

        for path in root_directory:
            if not self.search_ipynb_cp(path): # Ignoring files that are checkpoints
                files_in_path = os.listdir(path)
                [total_list.append(self.dir_file(path, f)) for f in files_in_path if self.search_jupyter_R(f) is not None]
        for i in total_list:
            print(i[1])

        #markdownfiles = GetMarkdownInfo(total_list, upp_funnel)

    def extract_req_files(self, path):
        pass

    def search_jupyter_R(self, file):
        ''' Returns file if its either a jupyter or R file '''
        if self.search_ipynb(file) or self.search_R(file):
            return file

    def search_ipynb_cp(self, path):
        ''' Return files that are part of the jupyter checkpoint directory'''
        return path.endswith(".ipynb_checkpoints")

    def search_ipynb(self, file):
        ''' Returns jupyter notebook files'''
        return file.endswith(".ipynb")

    def search_R(self, file):
        ''' Returns R files '''
        return file.endswith(".R")

    def dir_file(self, path, file):
        ''' Returns a list with the file appeneded to the path and only the path'''
        path_file = path + '/' + file
        return [path, path_file]

class GetMarkdownInfo:
    ''' Converts juypter notebook to markdown. '''
    def __init__(self, total_list, uppers_funnels):
        self.total_list = total_list
        self.uppfunnel = uppers_funnels
        self.reading_files(self.total_list, self.uppfunnel)

    ''' Computes the headers for the files'''
    def reading_files(self, total_list, uppfunnel):
        all_json = self.extract_markdowns(total_list)
        sub_headers = self.markdown_subheaders(all_json, uppfunnel)

        CreateFrame(sub_headers)

    def include_all_files(self, total_list):
        ''' Returns a list of all the files and their path (files that are not markdowns)'''

        arranged_list = []
        for single_list in total_list:
            extract_filename = self.last_instance(single_list[1])
            extract_subdirectory = self.last_instance(extract_filename[0])
            arranged_data = self.array_info(extract_filename, extract_subdirectory)
            arranged_list.append(arranged_data)

        return arranged_list

    def array_info(self, app_file, app_dir):
        file_needed = app_file[1]
        path, subdir = app_dir
        return [path, subdir, [file_needed]]

    def full_path_string(self, pathname):
        return pathname[1]

    def extract_markdowns(self, compiled_list):
        ''' Returns json and merges w/ path file.'''

        all_json_files = []
        for single_file in compiled_list:
            path_name, path_name_file = self.appr_paths(single_file)

            with open(path_name_file) as filename:
                try:
                    json_file = self.upload_json(filename)
                    if json_file is not None:
                        all_json_files.append([json_file, path_name, path_name_file])

                except json.decoder.JSONDecodeError:
                    pass

        return all_json_files

    ''' Extracting the content from the markdown cells. '''
    def markdown_subheaders(self, headers, uppfunnel):

        sub_headers = []
        for header in headers:
            list_subheaders = []
            update_path, new_file, source_info, file_header = self.parse_imp_data(header, uppfunnel)

            list_subheaders.append(file_header)

            for source_info in source_info:
                try:
                    topic = self.main_topic(source_info)
                    if topic is not None:
                        list_subheaders.append(topic)

                    if [update_path, new_file, list_subheaders] not in sub_headers:
                        sub_headers.append([update_path, new_file, list_subheaders])
                except IndexError:
                    pass
        return sub_headers

    def parse_imp_data(self, header, uppfunnel):
        new_path_name, new_file = self.scrape_file_info(header, uppfunnel)
        all_sources_info = self.scrape_source_info(header)
        file_header = self.dir_filename(header)
        return [new_path_name, new_file, all_sources_info, file_header]

    def appr_paths(self, single_file):
        return [single_file[0], single_file[1]]

    def upload_json(self, filename):
        return self.markddown_files(json.load(filename))

    ''' Extract #1 Header from markdown. '''
    def markddown_files(self, json_format):
        for (key, value) in json_format.items():
            if type(value) is list: # juypter notebook contains additional dictionary which we do not need
                if value[0]['cell_type'] == "markdown":
                    return value

    def dir_filename(self, header):
        return header[2].split('/')[-1]

    def scrape_source_info(self, header):
        return header[0]

    def scrape_file_info(self, header, uppfunnel):
        path_name = header[1]
        new_path, new_file = self.last_instance(path_name, uppfunnel)
        return [new_path, new_file]

    def main_topic(self, source):
        topic = source['source'][0]
        if topic.startswith('#'):
            return self.cleaned_topic(topic)

    def cleaned_topic(self, topic):
        topic = topic.strip('#')
        topic = topic.lstrip()
        topic = topic.rstrip('\n')
        return topic

    ''' Returns last instance of /, which separates directories'''
    def last_instance(self, full_path, uppfunnel):
        for dir in uppfunnel:
            length = len(dir)
            instance_pos = full_path.find(dir)

            if instance_pos != -1:
                path = self.updated_pathname(full_path, instance_pos+length, uppfunnel)
                file = self.updated_file(full_path, instance_pos+length)
                return [path, file]

    def updated_pathname(self, path, instance, uppfunnel):
        return path[0:instance]

    def updated_file(self, path, instance):
        return path[instance+1:].split('/')

class CreateFrame:
    def __init__(self, topics):
        self.topics = topics
        self.entire_dict = {}
        self.full_list = []
        self.entire_dict_2 = self.rec_dd()
        framework_of_files = self.second_framework(topics)

        #BuildTemplate(framework_of_files)

    def second_framework(self, topics):
        total_dicts = {}

        for per_topic in topics:
            main_topic, sub_topic, *rest_topics = self.split_headerlist(per_topic)
            main_topic = [main_topic]
            totaltopics = main_topic + sub_topic

            new_dict = current = {}
            for sub_per_topic in totaltopics:
                if sub_per_topic is not totaltopics[-1]:

                    current[sub_per_topic] = {}
                    current = current[sub_per_topic]
                    #frame[sub_per_topic] = current[sub_per_topic]

                else:
                    current[sub_per_topic] = rest_topics
                    current = current[sub_per_topic]

if __name__ == "__main__":
    SearchInformation()
