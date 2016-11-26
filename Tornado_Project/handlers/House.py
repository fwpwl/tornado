# coding:utf-8

import logging
import constants
import json

from .BaseHandler import BaseHandler
from utils.response_code import RET
from utils.common import require_logined
from config import image_url_prefix

class AreaInfoHandler(BaseHandler):
    """"""
    def get(self):
        # 先从Redis中获取数据
        try:
            ret = self.redis.get("area_info")
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            logging.debug(ret)
            logging.info("hit redis cache")
            return self.write('{"errno":%s, "errmsg":"OK", "data":%s}' % (RET.OK, ret))
        # 未从Redis中拿到数据，去数据库查询
        try:
            ret = self.db.query("select ai_area_id,ai_name from ih_area_info")
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="get data error"))
        if not ret:
            return self.write(dict(errno=RET.NODATA, errmsg="no area data"))
        areas = []
        for l in ret:
            area = {
                "area_id":l["ai_area_id"],
                "name":l["ai_name"]
            }
            areas.append(area)
        # 将数据缓存到Redis中
        try:
            self.redis.setex("area_info", constants.AREA_INFO_REDIS_EXPIRES_SECONDS, json.dumps(areas))
        except Exception as e:
            logging.error(e)
        # 返回客户端
        self.write(dict(errno=RET.OK, errmsg="OK", data=areas))


class MyHousesHandler(BaseHandler):
    """"""
    @require_logined
    def get(self):
        user_id = self.session.data["user_id"]
        try:
            ret = self.db.query("select a.hi_house_id,a.hi_title,a.hi_price,a.hi_ctime,b.ai_name,a.hi_index_image_url from ih_house_info a left join ih_area_info b on a.hi_area_id=b.ai_area_id where a.hi_user_id=%s;", user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errno":RET.DBERR, "errmsg":"get data erro"})
        houses = []
        if ret:
            for l in ret:
                house = {
                    "house_id":l["hi_house_id"],
                    "title":l["hi_title"],
                    "price":l["hi_price"],
                    "ctime":l["hi_ctime"].strftime("%Y-%m-%d"),
                    "area_name":l["ai_name"],
                    "img_url":image_url_prefix + l["hi_index_image_url"] if l["hi_index_image_url"] else ""
                }
                houses.append(house)
        self.write({"errno":RET.OK, "errmsg":"OK", "houses":houses})



