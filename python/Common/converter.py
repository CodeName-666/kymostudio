from typing import Any

from PySide6.QtQml import QJSValue
from Logger import logger


class Converter:
    @staticmethod
    def list_to_jsvalue(data_list):
        value = QJSValue()
        for i in range(len(data_list)):
            logger.log_debug('key = {}: | value = {} | type = {}'.format(
                i, data_list[i], type(data_list[i])))
            if isinstance(data_list[i], dict):
                sub_value = Converter.dict_to_jsvalue(data_list[i])
                value.setProperty(i, sub_value)
            elif isinstance(data_list[i], list):
                sub_value = Converter.list_to_jsvalue(data_list[i])
                value.setProperty(i, sub_value)
            else:
                value.setProperty(i, data_list[i])
        return value

    @staticmethod
    def dict_to_jsvalue(data_dict):
        value = QJSValue()
        for (k, v) in data_dict.items():
            logger.log_debug(
                'key = {}: | value = {} | type = {}'.format(k, v, type(v)))
            if isinstance(v, dict):
                sub_value = Converter.dict_to_jsvalue(v)
                value.setProperty(k, sub_value)
            elif isinstance(v, list):
                sub_value = Converter.list_to_jsvalue(v)
                value.setProperty(k, sub_value)
            else:
                value.setProperty(k, v)
        return value

    @staticmethod
    def jsvalue_to_dict(jsvalue: Any):
        if isinstance(jsvalue, QJSValue):
            variant = jsvalue.toVariant()
        else:
            variant = jsvalue

        return Converter.__convert_variant(variant)

    @staticmethod
    def __convert_variant(value: Any):
        if isinstance(value, QJSValue):
            return Converter.jsvalue_to_dict(value)

        if isinstance(value, dict):
            return {k: Converter.__convert_variant(v) for k, v in value.items()}

        if isinstance(value, (list, tuple)):
            return [Converter.__convert_variant(v) for v in value]

        return value
