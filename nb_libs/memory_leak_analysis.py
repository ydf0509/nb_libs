import gc
import sys

import objgraph
from nb_log import LoggerMixinDefaultWithFileHandler

class MemoryLeakAnalysis(LoggerMixinDefaultWithFileHandler):
    mla_flag = '内存排查自身对象标志-'

    @staticmethod
    def _get_obj_len(obj):
        try:
            return len(obj)
        except Exception:
            return -1

    @staticmethod
    def _dict_sort(dictx:dict,sort_k:str):
        items_list:list = list(dictx.items())
        items_list.sort(key=lambda x:x[1][sort_k],reverse=True)
        return dict(items_list)

    @staticmethod
    def _judge_contains_words(obj,word_list):
        for word in word_list:
            if word in str(obj):
                return True
        return False


    def show_max_obj(self):
        type_cnt_list= objgraph.most_common_types(limit=10000 *10000)
        # self.logger.debug(type_cnt_list)
        # self.logger.debug(len(type_cnt_list))
        type__max_size_map= {}
        type__max_obj_map = {}
        for typex,cnt in type_cnt_list:
            # if typex != 'dict':
            #     continue
            # print(typex)
            obj_list = objgraph.by_type(typex)


            max_len_obj = None
            max_str_len_obj = None
            max_size_obj = None
            max_len=0
            max_str_len = 0
            max_size = 0
            for obj in obj_list:
                # if  not self._judge_contains_words(obj,[self.mla_flag]):
                if 'many str in dict' in str(obj):
                    print(obj.keys())
                    print(len(obj), len(str(obj)), sys.getsizeof(obj))
                if self.mla_flag not in str(obj):
                    if self._get_obj_len(obj) > max_len :
                        max_len = self._get_obj_len(obj)
                        max_len_obj = obj
                    if len(str(obj))  > max_str_len:
                        max_str_len = len(str(obj))
                        max_str_len_obj = obj
                    if sys.getsizeof(obj) >max_size:
                        max_size = sys.getsizeof(obj)
                        max_size_obj = obj


            type__max_size_map[typex] = {f'{self.mla_flag}max_len': max_len, f'{self.mla_flag}max_str_len': max_str_len,f'{self.mla_flag}max_size': max_size}
            type__max_obj_map[typex] = {f'{self.mla_flag}max_len_obj':max_len_obj,f'{self.mla_flag}max_str_len_obj':max_str_len_obj,f'{self.mla_flag}max_size_obj':max_size_obj}

        # self.logger.debug(type__max_size_map)
        self.logger.debug(self._dict_sort(type__max_size_map,f'{self.mla_flag}max_size'))
        # self.logger.debug(self._dict_sort(type__max_size_map, f'{self.mla_flag}max_str_len_obj')['__name__'])
        self.logger.debug(type__max_obj_map['dict'][f'{self.mla_flag}max_str_len_obj'])
        # for ref in gc.get_referrers(type__max_obj_map['dict'][f'{self.mla_flag}max_size_obj']):
        #     if self.mla_flag not in str(ref):
        #         self.logger.debug(ref)


    def start(self):
        pass


if __name__ == '__main__':
    import aiomysql
    mla = MemoryLeakAnalysis()
    mla.show_max_obj()
