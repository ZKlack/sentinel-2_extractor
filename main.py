from sentinelhub import SHConfig #set config for sentinelhub
from dotenv import load_dotenv
import os
import argparse
from datetime import datetime, timedelta, timezone
from sentinelhub import SentinelHubRequest, DataCollection, MimeType, BBox, CRS, SentinelHubDownloadClient, filter_times
from dateutil.relativedelta import relativedelta

load_dotenv()  # Load environment variables from .env file

config = SHConfig()
config.instance_id = os.getenv('INSTANCE_ID')
config.sh_client_id = os.getenv('SH_CLIENT_ID')
config.sh_client_secret = os.getenv('SH_CLIENT_SECRET')

def parse_args():
    parser = argparse.ArgumentParser(description="Sentinel-2 Extractor")
    parser.add_argument('min_lon', type=float, help='Minimum longitude')
    parser.add_argument('min_lat', type=float, help='Minimum latitude')
    parser.add_argument('max_lon', type=float, help='Maximum longitude')
    parser.add_argument('max_lat', type=float, help='Maximum latitude')
    now = datetime.now(tz=timezone.utc)
    one_year_ago = now - timedelta(days=365)
    parser.add_argument('--start_date', type=str, default=one_year_ago.strftime('%Y-%m-%d'), help='Start date (YYYY-MM-DD), default: one year ago')
    parser.add_argument('--end_date', type=str, default=now.strftime('%Y-%m-%d'), help='End date (YYYY-MM-DD), default: today')
    parser.add_argument('--interval', type=str, default='1M', help='Interval, default: 1M (one month)')
    return parser.parse_args()

args = parse_args()
bbox = [args.min_lon, args.min_lat, args.max_lon, args.max_lat]
start_date = args.start_date
end_date = args.end_date
interval = args.interval
