import logging
import re
import time
import requests
import json
from auth.models import models
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http.response import HttpResponseNotFound, HttpResponseServerError, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status


'''
0 没有错误
1 未知错误  针对此错误  线上版前端弹出网络错误等公共错误
2 前端弹窗错误(包括：字段验证错误、自定义错误、账号或数据不存在、提示错误)
'''


class PUTtoPATCHMiddleware(MiddlewareMixin):
    '''将 put 请求转为 patch 请求 中间件'''
    
    def process_request(self, request):
        if request.method == 'PUT':
            request.method = 'PATCH'


class LogMiddleware(MiddlewareMixin):
    '''日志中间件'''
    
    def process_request(self, request):
        try:
            logging.info('************************************************* 下面是新的一条日志 ***************************************************')
            logging.info('拦截请求的地址：%s；请求的方法：%s' % (request.path, request.method))
            logging.info('==================================== headers 头信息 ====================================================')
            for key in request.META:
                if key[:5] == 'HTTP_':
                    logging.debug('%s %s' % (str(key), str(request.META[key])))
            logging.debug(f"Content-Type {request.META.get('CONTENT_TYPE')}")
            logging.info('代理IP：%s' % request.META.get('REMOTE_ADDR'))
            logging.info('真实IP：%s' % request.META.get('HTTP_X_FORWARDED_FOR'))   # HTTP_X_REAL_IP
            logging.info('==================================== request body信息 ==================================================')
            logging.info('params参数：%s' % request.GET)
            if request.content_type in ('application/json', 'text/plain', 'application/xml'):
                if request.path not in ('/callpresell/', ):
                    logging.info('body参数：%s' % request.body.decode())
            if request.content_type in ('multipart/form-data', 'application/x-www-form-urlencoded'):
                logging.info('是否存在文件类型数据：%s', bool(request.FILES))
                logging.info('data参数：%s', request.POST)
            logging.info('================================== View视图函数内部信息 ================================================')
            if request.method in {'DELETE', 'delete'}:
                logging.info(f"{'>'*9} 发现删除数据 {'<'*9}")
                logging.info(f"删除请求的地址：{request.path}，执行用户：{request.user}")
        except Exception as e:
            logging.error('未知错误：%s' % str(e))
            return JsonResponse({"msg": "请求日志输出异常：%s" % e, "code": 1, "data": {}})

    def process_exception(self, request, exception):
        logging.error('发生错误的请求地址：{}；错误原因：{}；错误详情：'.format(request.path, str(exception)))
        logging.exception(exception)
        return JsonResponse({"msg": "An unexpected view error occurred: %s" % exception.__str__(), "code": 1, "data": {}})
    
    def process_response(self, request, response):
        if settings.SHOWSQL:
            for sql in connection.queries:
                logging.debug(sql)
        return response


class PermissionMiddleware(MiddlewareMixin):
    '''接口加密中间件'''
    def process_request(self, request):
        white_paths = ['/', '/__debug__/', '/__debug__', '/favicon.ico']
        if request.path not in white_paths and not re.match(r'/swagger.*', request.path, re.I) and not re.match(r'/redoc/.*', request.path, re.I) and not re.match(r'/export.*', request.path, re.I):
            # print('查看authkey',request.META.get('HTTP_INTERFACEKEY'))
            # auth_key = request.META.get('token') # key顺序必须符合要求：毫秒时间戳+后端分配的key+32位随机字符串(uuid更佳)
            print(request.META.get('HTTP_TOKEN'))
            auth_key =request.META.get('HTTP_TOKEN')
            if auth_key:
                # print('查看秘钥：', cache.get(auth_key))
                # if cache.get(auth_key):
                #     logging.info('发现秘钥被多次使用，应当记录ip加入预备黑名单。')
                #     return JsonResponse({"msg": "非法访问！已禁止操作！", "code": 10, "data": {}})
                print(settings.SSO_TOKEN_URL)
                # 先解密
                target_key = auth_key
                # 无法解密时直接禁止访问
                if not target_key: return JsonResponse({"msg": "非法访问！已禁止操作！" , "code": 10, "data": {}})
                # 解密成功后
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5',
                    'token': auth_key
                }
                response = requests.get(settings.SSO_TOKEN_URL, headers=headers)
                logging.info("result:{}",response)
                print(response)
                result = json.loads(response.text)
                if result is None:
                    return JsonResponse({"msg": "接口token校验失败！禁止访问！", "code": 500, "data": {}})
                if result['code'] != 200 and result['success'] != 'True':
                    return JsonResponse({"msg": "接口token校验失败！禁止访问！", "code": result.code, "data":result['message']})
                # 设置一个redis 记录当前时间戳
                time_int = int(time.time()) # 记录秒
                # target_time, backend_key, random_str = target_key.split('+')
                # if backend_key not in settings.DISPATCH_KEYS: return JsonResponse({"msg": "非法访问！已禁止操作！" , "code": 10, "data": {}})
                # if (time_int - int(int(target_time) / 1000)) > settings.INTERFACE_TIMEOUT:
                #     logging.info('发现秘钥被多次使用，应当记录ip加入预备黑名单。')
                #     return JsonResponse({"msg": "非法访问！已禁止操作！" , "code": 10, "data": {}})
                # cache.set(auth_key, "true", timeout=settings.INTERFACE_TIMEOUT)
                pass
            else:
                return JsonResponse({"msg": "接口秘钥未找到！禁止访问！" , "code": 10, "data": {}})


class FormatReturnJsonMiddleware(MiddlewareMixin):
    '''格式化 response 中间件'''
    
    def process_response(self, request, response):
        try:
            if isinstance(response, HttpResponseNotFound): 
                return JsonResponse({"msg": response.reason_phrase, "code": 2,"data": {}}, status=response.status_code)
            if isinstance(response, HttpResponseServerError): 
                return JsonResponse({"msg": response.reason_phrase, "code": 1,"data": {}}, status=response.status_code)
            if response.status_code == 204:
                return JsonResponse({"msg": 'delete success', "code": 0,"data": {}}, status=status.HTTP_200_OK)
            # print('-'*128)
        except Exception as e:
            logging.exception(e)
        return response

