from sentinelhub import SHConfig #set config for sentinelhub
from dotenv import load_dotenv
import os
import argparse
from datetime import datetime, timedelta, timezone
from sentinelhub import SentinelHubRequest, DataCollection, MimeType, BBox, CRS, SentinelHubDownloadClient, filter_times
from dateutil.relativedelta import relativedelta
import rasterio
import numpy as np
import math

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

def get_time_intervals(start, end, interval):
    # interval: '1M' for one month, '1D' for one day, etc.
    intervals = []
    current = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    while current < end_dt:
        if interval.endswith('M'):
            next_time = current + relativedelta(months=int(interval[:-1] or 1))
        elif interval.endswith('D'):
            next_time = current + timedelta(days=int(interval[:-1] or 1))
        else:
            raise ValueError("Unsupported interval format")
        intervals.append((current.strftime("%Y-%m-%d"), min(next_time, end_dt).strftime("%Y-%m-%d")))
        current = next_time
    return intervals

bbox_obj = BBox(bbox, crs=CRS.WGS84)
time_intervals = get_time_intervals(start_date, end_date, interval)

evalscript = """
//VERSION=3
function setup() {
  return {
    input: ["B02", "B04", "B08", "B11"],
    output: { bands: 4, sampleType: "UINT16" }
  };
}
function evaluatePixel(sample) {
  return [sample.B02, sample.B04, sample.B08, sample.B11];
}
"""

def make_size(bbox_obj, resolution):
	# 1 degree of latitude ~= 111,320 meters
	hight = ((bbox_obj.max_y - bbox_obj.min_y) * 111320 ) / resolution
	# 1 degree of longitude ~= 111,320 * cos(latitude) meters
	width = ((bbox_obj.max_x - bbox_obj.min_x) * 111320 * math.cos(math.radians((bbox_obj.max_y + bbox_obj.min_y)/2))) / resolution
	return (int(width), int(hight))

requests = []
for t_start, t_end in time_intervals:
    req = SentinelHubRequest(
        data_folder='./pulled_data',
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(t_start, t_end),
                mosaicking_order='mostRecent',
                other_args={"maxCloudCoverage": 30}
            )
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.TIFF)
        ],
        bbox=bbox_obj,
        size=make_size(bbox_obj, 10),
        config=config
    )
    requests.append(req)


def save_tiff(array, reference_src, out_path):
	profile = reference_src.profile
	profile.update(
		dtype=rasterio.float32,
		count=1,
		compress='lzw'
	)
	with rasterio.open(out_path, 'w', **profile) as dst:
		dst.write(array.astype(np.float32), 1)


band_names = {
	"B02": ("Blue", 1),
	"B04": ("Red", 2),
	"B08": ("NIR", 3),
	"B11": ("SWIR", 4)
}

for i, req in enumerate(requests):
	(t_start, t_end) = time_intervals[i]
	timewindow = f"{t_start}_{t_end}"
	current_subdirs = os.listdir("./pulled_data")
	data = req.get_data(save_data=True)

	if req.download_list:
		response_id = [d for d in os.listdir("./pulled_data") if d not in current_subdirs][0]
		response_path = os.path.join("./pulled_data", response_id, "response.tiff")
		print(f"Downloaded interval {i}: {response_path}")

		indices_dir = os.path.join("./formatted_data", timewindow, "indices")
		rays_dir = os.path.join("./formatted_data", timewindow, "rays")
		os.makedirs(indices_dir, exist_ok=True)
		os.makedirs(rays_dir, exist_ok=True)

		with rasterio.open(response_path) as src:
			# Extract bands
			blue = src.read(band_names["B02"][1]).astype(np.float32)
			red  = src.read(band_names["B04"][1]).astype(np.float32)
			nir  = src.read(band_names["B08"][1]).astype(np.float32)
			swir = src.read(band_names["B11"][1]).astype(np.float32)

			# Save rays
			save_tiff(blue, src, os.path.join(rays_dir, "Blue.tiff"))
			save_tiff(red,  src, os.path.join(rays_dir, "Red.tiff"))
			save_tiff(nir,  src, os.path.join(rays_dir, "NIR.tiff"))
			save_tiff(swir, src, os.path.join(rays_dir, "SWIR.tiff"))

			# Indices
			ndvi = (nir - red) / (nir + red + 1e-6)
			save_tiff(ndvi, src, os.path.join(indices_dir, "NDVI.tiff"))

			ndmi = (nir - swir) / (nir + swir + 1e-6)
			save_tiff(ndmi, src, os.path.join(indices_dir, "NDMI.tiff"))

			bsi = ((swir + red) - (nir + blue)) / ((swir + red) + (nir + blue) + 1e-6)
			save_tiff(bsi, src, os.path.join(indices_dir, "BSI.tiff"))

			savi = (nir - red) / (nir + red + 0.5 + 1e-6)
			save_tiff(savi, src, os.path.join(indices_dir, "SAVI.tiff"))

			evi = (nir - red) / (nir - (6 * red) - (7.5 * blue) + 1 + 1e-6)
			save_tiff(evi, src, os.path.join(indices_dir, "EVI.tiff"))

		print(f"Processed {timewindow} → indices + rays saved.")

	else:
		print(f"No data downloaded for interval {i}.")
