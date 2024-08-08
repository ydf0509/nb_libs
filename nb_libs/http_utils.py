from urllib.parse import parse_qs,parse_qsl,urlencode,quote_plus
from itertools import chain
class BodyParser(object):
    @classmethod
    def formdata_to_dict(cls, query_string):
        body_dict = parse_qs(query_string)
        body_dict_new = {}
        for k,v in body_dict.items():
            if len(v)>1:
                body_dict_new[k] = v
            else:
                body_dict_new[k]=v[0]
        return body_dict_new

    @classmethod
    def dict_to_query_string(cls, body_dict):
        parts = []
        for key, value in body_dict.items():
            if isinstance(value, list):
                # 对于列表，我们将其元素转换为'key[index]=value'的形式
                for index, item in enumerate(value):
                    parts.append(f"{quote_plus(key)}={quote_plus(str(item))}")
            else:
                # 对于非列表值，直接转换为'key=value'
                parts.append(f"{quote_plus(key)}={quote_plus(str(value))}")
        return '&'.join(parts)




if __name__ == '__main__':
    query_string = "name=John+Doe&age=30&age=31&city=New+York"
    print(BodyParser.formdata_to_dict(query_string))

    body_dict = {'name': 'John Doe', 'age': ['30', '31'], 'city': 'New York'}
    print(BodyParser.dict_to_query_string(body_dict))