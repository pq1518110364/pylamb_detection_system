import logging
from utils.RedisCli import RedisCli, RedisHash
from rest_framework.views import APIView
from extensions.MyResponse import MyJsonResponse

# Create your views here.
class TestView(APIView):
    # @swagger_auto_schema(operation_summary="测试接口", operation_description="新建的测试接口")
    def get(self, request):
        """测试接口"""
        logging.info('test' * 3)
        redis_cli = RedisCli()
        conn = redis_cli.coon
        # value = conn.get('test')
        # logging.info(value)
        result = conn.get('test')
        logging.info(result)
        response = MyJsonResponse({'msg': 'success'}, 200, {})
        return
