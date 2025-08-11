# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather information using the Hefeng Weather API. This server supports both Chinese and international cities with multiple fallback methods for location resolution.

## Features

- 🌤️ **3-day weather forecast** for any city
- 🌡️ **Current weather** information
- 🚨 **Weather alerts** for US states (using NWS API)
- 🇨🇳 **Chinese city support** with predefined city IDs
- 🌍 **International city support** via geocoding
- 🔄 **Multiple fallback methods** for location resolution

## Supported Cities

The server includes predefined support for major Chinese cities:
- Beijing (北京), Shanghai (上海), Guangzhou (广州), Shenzhen (深圳)
- Hangzhou (杭州), Nanjing (南京), Wuhan (武汉), Chengdu (成都)
- And many more...

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd weatherMCP
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Get your Hefeng Weather API JWT token from [Hefeng Weather](https://dev.qweather.com/)
2. Copy `config_template.py` to `config.py`:
   ```bash
   cp config_template.py config.py
   ```
3. Edit `config.py` and replace `YOUR_JWT_TOKEN_HERE` with your actual JWT token
4. The `config.py` file is already added to `.gitignore` to keep your token secure

## Usage

### Running the MCP Server

```bash
python get_weather_MCP.py
```

The server will start and listen for MCP client connections via stdio.

### Available Tools

#### Get Weather Forecast
```python
get_forecast(city: str) -> str
```
Get a 3-day weather forecast for any city.

Example:
- `get_forecast("北京")` - Beijing weather forecast
- `get_forecast("New York")` - New York weather forecast

#### Get Current Weather
```python
get_current_weather(city: str) -> str
```
Get current weather information for any city.

Example:
- `get_current_weather("上海")` - Shanghai current weather
- `get_current_weather("London")` - London current weather

#### Get Weather Alerts
```python
get_weather_alerts(state: str) -> str
```
Get weather alerts for US states using NWS API.

Example:
- `get_weather_alerts("CA")` - California weather alerts
- `get_weather_alerts("NY")` - New York weather alerts

## Architecture

### Location Resolution
The server uses multiple fallback methods to resolve city names:

1. **Hefeng Weather API** - Primary geocoding service
2. **Geopy** - Secondary geocoding for international cities
3. **Predefined Cities** - Fast lookup for major Chinese cities
4. **Fuzzy Matching** - Partial name matching

### API Integration
- **Primary**: Hefeng Weather API (Chinese cities)
- **Secondary**: NWS API (US weather alerts)
- **Fallback**: Geopy geocoding (international cities)

## Dependencies

- `mcp-server-fastmcp` - FastMCP framework
- `httpx` - HTTP client
- `geopy` - Geocoding library

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Security

- **API Tokens**: Never commit your actual JWT token to version control
- **Configuration**: The `config.py` file is excluded from git tracking via `.gitignore`
- **Template**: Use `config_template.py` as a starting point for your configuration
- **Environment Variables**: For production, consider using environment variables instead of config files

## Support

For issues and questions, please open an issue on GitHub.

