#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 服务器：天气查询服务
使用 FastMCP 框架，通过标准输入/输出与 MCP 客户端通信，提供天气信息查询。
"""

import sys
import httpx
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Initialize FastMCP server
mcp = FastMCP("weather", log_level="ERROR")

# ------------------------------ 配置 ------------------------------

# Import configuration from separate file
from config import HEFENG_JWT_TOKEN, HEFENG_FORECAST_URL, HEFENG_NOW_URL, HEFENG_LOCATION_URL

# 地理编码器 (用于将城市名转为经纬度或ID)
geolocator = Nominatim(user_agent="mcp_weather_server")

# 预定义的主要城市ID (和风天气API格式)
PREDEFINED_CITIES = {
    '北京': {'id': '101010100', 'name': '北京', 'adm2': '北京市', 'country': '中国'},
    '上海': {'id': '101020100', 'name': '上海', 'adm2': '上海市', 'country': '中国'},
    '广州': {'id': '101280101', 'name': '广州', 'adm2': '广东省', 'country': '中国'},
    '深圳': {'id': '101280601', 'name': '深圳', 'adm2': '广东省', 'country': '中国'},
    '杭州': {'id': '101210101', 'name': '杭州', 'adm2': '浙江省', 'country': '中国'},
    '南京': {'id': '101190101', 'name': '南京', 'adm2': '江苏省', 'country': '中国'},
    '武汉': {'id': '101200101', 'name': '武汉', 'adm2': '湖北省', 'country': '中国'},
    '成都': {'id': '101270101', 'name': '成都', 'adm2': '四川省', 'country': '中国'},
    '西安': {'id': '101110101', 'name': '西安', 'adm2': '陕西省', 'country': '中国'},
    '天津': {'id': '101030100', 'name': '天津', 'adm2': '天津市', 'country': '中国'},
    '重庆': {'id': '101040100', 'name': '重庆', 'adm2': '重庆市', 'country': '中国'},
    '青岛': {'id': '101120201', 'name': '青岛', 'adm2': '山东省', 'country': '中国'},
    '大连': {'id': '101070201', 'name': '大连', 'adm2': '辽宁省', 'country': '中国'},
    '厦门': {'id': '101230201', 'name': '厦门', 'adm2': '福建省', 'country': '中国'},
    '苏州': {'id': '101190401', 'name': '苏州', 'adm2': '江苏省', 'country': '中国'},
    '无锡': {'id': '101190201', 'name': '无锡', 'adm2': '江苏省', 'country': '中国'},
    '宁波': {'id': '101210401', 'name': '宁波', 'adm2': '浙江省', 'country': '中国'},
    '长沙': {'id': '101250101', 'name': '长沙', 'adm2': '湖南省', 'country': '中国'},
    '郑州': {'id': '101180101', 'name': '郑州', 'adm2': '河南省', 'country': '中国'},
    '济南': {'id': '101120101', 'name': '济南', 'adm2': '山东省', 'country': '中国'},
    '哈尔滨': {'id': '101050101', 'name': '哈尔滨', 'adm2': '黑龙江省', 'country': '中国'},
    '沈阳': {'id': '101070101', 'name': '沈阳', 'adm2': '辽宁省', 'country': '中国'},
    '长春': {'id': '101060101', 'name': '长春', 'adm2': '吉林省', 'country': '中国'},
    '石家庄': {'id': '101090101', 'name': '石家庄', 'adm2': '河北省', 'country': '中国'},
    '太原': {'id': '101100101', 'name': '太原', 'adm2': '山西省', 'country': '中国'},
    '呼和浩特': {'id': '101080101', 'name': '呼和浩特', 'adm2': '内蒙古自治区', 'country': '中国'},
    '南昌': {'id': '101240101', 'name': '南昌', 'adm2': '江西省', 'country': '中国'},
    '福州': {'id': '101230101', 'name': '福州', 'adm2': '福建省', 'country': '中国'},
    '合肥': {'id': '101220101', 'name': '合肥', 'adm2': '安徽省', 'country': '中国'},
    '昆明': {'id': '101290101', 'name': '昆明', 'adm2': '云南省', 'country': '中国'},
    '贵阳': {'id': '101260101', 'name': '贵阳', 'adm2': '贵州省', 'country': '中国'},
    '南宁': {'id': '101300101', 'name': '南宁', 'adm2': '广西壮族自治区', 'country': '中国'},
    '海口': {'id': '101310101', 'name': '海口', 'adm2': '海南省', 'country': '中国'},
    '兰州': {'id': '101160101', 'name': '兰州', 'adm2': '甘肃省', 'country': '中国'},
    '西宁': {'id': '101150101', 'name': '西宁', 'adm2': '青海省', 'country': '中国'},
    '银川': {'id': '101170101', 'name': '银川', 'adm2': '宁夏回族自治区', 'country': '中国'},
    '乌鲁木齐': {'id': '101130101', 'name': '乌鲁木齐', 'adm2': '新疆维吾尔自治区', 'country': '中国'},
    '拉萨': {'id': '101140101', 'name': '拉萨', 'adm2': '西藏自治区', 'country': '中国'},
    '台北': {'id': '101340101', 'name': '台北', 'adm2': '台湾省', 'country': '中国'},
    '香港': {'id': '101320101', 'name': '香港', 'adm2': '香港特别行政区', 'country': '中国'},
    '澳门': {'id': '101330101', 'name': '澳门', 'adm2': '澳门特别行政区', 'country': '中国'},
}

# ----------------------------------------------------------------

async def make_hefeng_request(url: str, params: dict = None) -> dict[str, Any] | None:
    """Make a request to the Hefeng Weather API with proper error handling."""
    headers = {
        'Authorization': f'Bearer {HEFENG_JWT_TOKEN}',
        'Accept': 'application/json'
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error making Hefeng API request: {e}", file=sys.stderr)
            return None

async def get_location_info(city_name: str) -> Optional[dict[str, Any]]:
    """Get location information for a city using multiple fallback methods."""
    
    # 1. 尝试和风天气地理编码 API
    params = {
        'location': city_name,
        'range': 'cn'  # 限制搜索范围为中国
    }
    data = await make_hefeng_request(HEFENG_LOCATION_URL, params)
    
    if data and data.get('code') == '200' and data.get('location'):
        return data['location'][0]
    
    # 2. 尝试 geopy 备用方案
    try:
        location = geolocator.geocode(city_name, timeout=10)
        if location:
            return {
                'id': f"{location.latitude},{location.longitude}",
                'name': city_name,
                'adm2': location.raw.get('address', {}).get('state', ''),
                'country': location.raw.get('address', {}).get('country', ''),
                'lat': location.latitude,
                'lon': location.longitude
            }
    except Exception as e:
        print(f"Geopy fallback error: {e}", file=sys.stderr)
    
    # 3. 尝试预定义城市
    if city_name in PREDEFINED_CITIES:
        return PREDEFINED_CITIES[city_name]
    
    # 4. 尝试模糊匹配
    for key, value in PREDEFINED_CITIES.items():
        if city_name in key or key in city_name:
            return value
    
    return None

def format_forecast(forecast_data: dict, location_info: dict) -> str:
    """Format forecast data into a readable string."""
    city_name = location_info['name']
    admin_area = location_info.get('adm2', '')
    country = location_info.get('country', '')
    
    result = f"天气预报 - {city_name}"
    if admin_area:
        result += f" ({admin_area})"
    if country:
        result += f", {country}"
    result += "\n\n"
    
    for day in forecast_data['daily']:
        result += f"📅 {day['fxDate']}\n"
        result += f"🌡️ 温度: {day['tempMin']}°C ~ {day['tempMax']}°C\n"
        result += f"☀️ 白天: {day['textDay']}\n"
        result += f"🌙 夜间: {day['textNight']}\n"
        result += f"💨 风向: {day['windDirDay']} {day['windScaleDay']}级\n"
        result += "─" * 30 + "\n"
    
    return result

def format_current_weather(current_data: dict, location_info: dict) -> str:
    """Format current weather data into a readable string."""
    city_name = location_info['name']
    admin_area = location_info.get('adm2', '')
    country = location_info.get('country', '')
    
    result = f"当前天气 - {city_name}"
    if admin_area:
        result += f" ({admin_area})"
    if country:
        result += f", {country}"
    result += "\n\n"
    
    now = current_data['now']
    result += f"🌡️ 温度: {now['temp']}°C\n"
    result += f"🌡️ 体感温度: {now['feelsLike']}°C\n"
    result += f"☁️ 天气: {now['text']}\n"
    result += f"💨 风向: {now['windDir']} {now['windScale']}级\n"
    result += f"💧 湿度: {now['humidity']}%\n"
    result += f"⏰ 观测时间: {now['obsTime']}\n"
    
    return result

@mcp.tool()
async def get_forecast(city: str) -> str:
    """Get 3-day weather forecast for a city.

    Args:
        city: The name of the city (e.g. 北京, 上海, New York)
    """
    # Get location information
    location_info = await get_location_info(city)
    if not location_info:
        return f"无法找到城市 '{city}' 的位置信息。请检查城市名称是否正确。"
    
    # Get forecast data
    params = {'location': location_info['id']}
    forecast_data = await make_hefeng_request(HEFENG_FORECAST_URL, params)
    
    if not forecast_data or forecast_data.get('code') != '200':
        return f"无法获取 '{city}' 的天气预报数据。"
    
    return format_forecast(forecast_data, location_info)

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city: The name of the city (e.g. 北京, 上海, New York)
    """
    # Get location information
    location_info = await get_location_info(city)
    if not location_info:
        return f"无法找到城市 '{city}' 的位置信息。请检查城市名称是否正确。"
    
    # Get current weather data
    params = {'location': location_info['id']}
    current_data = await make_hefeng_request(HEFENG_NOW_URL, params)
    
    if not current_data or current_data.get('code') != '200':
        return f"无法获取 '{city}' 的当前天气数据。"
    
    return format_current_weather(current_data, location_info)

@mcp.tool()
async def get_weather_alerts(state: str) -> str:
    """Get weather alerts for a US state (using NWS API as fallback).

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    # This is kept as a fallback using NWS API for US alerts
    url = f"https://api.weather.gov/alerts/active/area/{state}"
    headers = {
        "User-Agent": "weather-app/1.0",
        "Accept": "application/geo+json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return "无法获取天气预警信息。"
    
    if not data or "features" not in data:
        return "无法获取预警信息或没有找到预警。"
    
    if not data["features"]:
        return f"该州 ({state}) 目前没有活跃的天气预警。"
    
    alerts = []
    for feature in data["features"]:
        props = feature["properties"]
        alert = f"""
事件: {props.get('event', '未知')}
地区: {props.get('areaDesc', '未知')}
严重程度: {props.get('severity', '未知')}
描述: {props.get('description', '无描述')}
指示: {props.get('instruction', '无具体指示')}
"""
        alerts.append(alert)
    
    return "\n---\n".join(alerts)

if __name__ == "__main__":
    # Initialize and run the server
    try:
        print("Starting MCP weather server...", file=sys.stderr)
        mcp.run(transport='stdio')
    except Exception as e:
        print(f"Error starting MCP server: {e}", file=sys.stderr)
        sys.exit(1)
