import asyncio
import traceback
import logging
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import DouYinVideo
from uploader.ks_uploader.main import KSVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day


def validate_and_generate_schedule(files, videos_per_day, daily_times, enable_timer, start_days, logger):
    """
    Safely generate schedule times with comprehensive validation to prevent list index errors.
    
    Returns:
        list: Safe publish times matching file count, or None if errors occur
    """
    try:
        file_count = len(files)
        if file_count == 0:
            logger.error("No video files provided")
            return None
        
        logger.info(f"Validating schedule generation: files={file_count}, per_day={videos_per_day}")
        
        # Validate daily_times
        if daily_times is None or len(daily_times) == 0:
            daily_times = [6, 11, 14, 16, 22]  # Safe default
            logger.info(f"Using safe default daily_times: {daily_times}")
        
        # Ensure daily_times is a proper list
        if not isinstance(daily_times, list):
            daily_times = [daily_times] if daily_times else [6, 11, 14, 16, 22]
        
        # Handle videos_per_day <= 0
        if videos_per_day <= 0:
            logger.warning(f"videos_per_day={videos_per_day} invalid, using 1")
            videos_per_day = 1
        
        # Handle start_days < 0
        if start_days < 0:
            logger.warning(f"start_days={start_days} invalid, using 0")
            start_days = 0
        
        # Handle mismatch between videos_per_day and daily_times length
        if videos_per_day > len(daily_times):
            available_slots = len(daily_times)
            logger.warning(f"videos_per_day({videos_per_day}) > available slots({available_slots})")
            videos_per_day = min(videos_per_day, available_slots)
            logger.info(f"Adjusted videos_per_day to: {videos_per_day}")
        
        # Generate schedule
        if enable_timer:
            try:
                publish_datetimes = generate_schedule_time_next_day(
                    file_count, videos_per_day, daily_times, False, start_days
                )
                
                # Final length validation
                if len(publish_datetimes) != file_count:
                    logger.error(f"Generated {len(publish_datetimes)} times for {file_count} files")
                    # Use immediate publishing as fallback
                    publish_datetimes = [0] * file_count
                    logger.warning("Using immediate publishing due to schedule generation issue")
                else:
                    logger.info(f"Successfully generated {len(publish_datetimes)} schedule times")
                    
            except Exception as e:
                logger.error(f"Schedule generation failed: {e}")
                publish_datetimes = [0] * file_count
                logger.warning("Using immediate publishing due to error")
        else:
            publish_datetimes = [0] * file_count
            logger.info(f"Using immediate publishing for {file_count} videos")
        
        return publish_datetimes
        
    except Exception as e:
        logger.error(f"Fatal error in validation: {e}")
        return [0] * len(files) if files else []

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def post_video_tencent(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    logger.info("=== Starting post_video_tencent with debug logging ===")
    
    try:
        logger.info(f"Parameters: title={title}, files={files}, account_file={account_file}")
        logger.info(f"tags={tags}, category={category}, enableTimer={enableTimer}")
        logger.info(f"videos_per_day={videos_per_day}, daily_times={daily_times}, start_days={start_days}")
        
        # 生成文件的完整路径
        logger.debug("Generating file paths...")
        account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
        files = [Path(BASE_DIR / "videoFile" / file) for file in files]
        
        logger.info(f"Resolved account files: {[str(f) for f in account_file]}")
        logger.info(f"Resolved video files: {[str(f) for f in files]}")
        
        if not files:
            logger.error("ERROR: No video files provided!")
            return
            
        if not account_file:
            logger.error("ERROR: No account files provided!")
            return
        
        logger.debug(f"Generating publish datetimes for {len(files)} files...")
        publish_datetimes = validate_and_generate_schedule(
            files, videos_per_day, daily_times, enableTimer, start_days, logger
        )
        
        if publish_datetimes is None:
            logger.error("Schedule generation failed - aborting upload")
            return
            
        logger.info(f"File count: {len(files)}, Datetime count: {len(publish_datetimes)}")
        logger.info(f"Scheduled publish times: {publish_datetimes}")
        
        for index, file in enumerate(files):
            logger.debug(f"Processing file {index}: {file}")
            if index >= len(publish_datetimes):
                logger.error(f"INDEX ERROR: index={index} >= len(datetimes)={len(publish_datetimes)}")
                continue
                
            for cookie_idx, cookie in enumerate(account_file):
                logger.debug(f"Processing cookie {cookie_idx} for file {index}")
                try:
                    logger.info(f"视频文件名：{file}")
                    logger.info(f"标题：{title}")
                    logger.info(f"Hashtag：{tags}")
                    datetime_to_use = publish_datetimes[index] 
                    logger.info(f"Using datetime: {datetime_to_use} (index: {index})")
                    app = TencentVideo(title, str(file), tags, datetime_to_use, cookie, category)
                    asyncio.run(app.main(), debug=False)
                except IndexError as e:
                    logger.error(f"IndexError during upload: {e}")
                    logger.error(f"Variables - index: {index}, file: {file}, dt_idx: {index}, datetimes_len: {len(publish_datetimes)}")
                    traceback.print_exc()
                except Exception as e:
                    logger.error(f"Exception in upload process: {e}")
                    traceback.print_exc()
                    
    except IndexError as e:
        logger.error(f"OUTER IndexError: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        traceback.print_exc()
    except Exception as e:
        logger.error(f"OUTER Exception: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        traceback.print_exc()


def post_video_DouYin(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    logger.info("=== Starting post_video_DouYin with debug logging ===")
    
    try:
        logger.info(f"Parameters: title={title}, files={files}, account_file={account_file}")
        logger.info(f"tags={tags}, category={category}, enableTimer={enableTimer}")
        logger.info(f"videos_per_day={videos_per_day}, daily_times={daily_times}, start_days={start_days}")
        
        # 生成文件的完整路径
        logger.debug("Generating file paths...")
        account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
        files = [Path(BASE_DIR / "videoFile" / file) for file in files]
        
        logger.info(f"Resolved account files: {[str(f) for f in account_file]}")
        logger.info(f"Resolved video files: {[str(f) for f in files]}")
        
        if not files:
            logger.error("ERROR: No video files provided!")
            return
            
        if not account_file:
            logger.error("ERROR: No account files provided!")
            return
        
        logger.debug(f"Generating publish datetimes for {len(files)} files...")
        publish_datetimes = validate_and_generate_schedule(
            files, videos_per_day, daily_times, enableTimer, start_days, logger
        )
        
        if publish_datetimes is None:
            logger.error("Schedule generation failed - aborting upload")
            return
            
        logger.info(f"File count: {len(files)}, Datetime count: {len(publish_datetimes)}")
        logger.info(f"Scheduled publish times: {publish_datetimes}")
        
        for index, file in enumerate(files):
            logger.debug(f"Processing file {index}: {file}")
            if index >= len(publish_datetimes):
                logger.error(f"INDEX ERROR: index={index} >= len(datetimes)={len(publish_datetimes)}")
                continue
                
            for cookie_idx, cookie in enumerate(account_file):
                logger.debug(f"Processing cookie {cookie_idx} for file {index}")
                try:
                    logger.info(f"文件路径{str(file)}")
                    logger.info(f"视频文件名：{file}")
                    logger.info(f"标题：{title}")
                    logger.info(f"Hashtag：{tags}")
                    datetime_to_use = publish_datetimes[index] 
                    logger.info(f"Using datetime: {datetime_to_use} (index: {index})")
                    app = DouYinVideo(title, str(file), tags, datetime_to_use, cookie, category)
                    asyncio.run(app.main(), debug=False)
                except IndexError as e:
                    logger.error(f"IndexError during upload: {e}")
                    logger.error(f"Variables - index: {index}, file: {file}, dt_idx: {index}, datetimes_len: {len(publish_datetimes)}")
                    traceback.print_exc()
                except Exception as e:
                    logger.error(f"Exception in upload process: {e}")
                    traceback.print_exc()
                    
    except IndexError as e:
        logger.error(f"OUTER IndexError: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        traceback.print_exc()
    except Exception as e:
        logger.error(f"OUTER Exception: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        traceback.print_exc()


def post_video_ks(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    logger.info("=== Starting post_video_ks with debug logging ===")
    
    try:
        logger.info(f"Parameters: title={title}, files={files}, account_file={account_file}")
        logger.info(f"tags={tags}, category={category}, enableTimer={enableTimer}")
        logger.info(f"videos_per_day={videos_per_day}, daily_times={daily_times}, start_days={start_days}")
        
        # 生成文件的完整路径
        logger.debug("Generating file paths...")
        account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
        files = [Path(BASE_DIR / "videoFile" / file) for file in files]
        
        logger.info(f"Resolved account files: {[str(f) for f in account_file]}")
        logger.info(f"Resolved video files: {[str(f) for f in files]}")
        
        if not files:
            logger.error("ERROR: No video files provided!")
            return
            
        if not account_file:
            logger.error("ERROR: No account files provided!")
            return
        
        logger.debug(f"Generating publish datetimes for {len(files)} files...")
        publish_datetimes = validate_and_generate_schedule(
            files, videos_per_day, daily_times, enableTimer, start_days, logger
        )
        
        if publish_datetimes is None:
            logger.error("Schedule generation failed - aborting upload")
            return
            
        logger.info(f"File count: {len(files)}, Datetime count: {len(publish_datetimes)}")
        logger.info(f"Scheduled publish times: {publish_datetimes}")
            
        for index, file in enumerate(files):
            logger.debug(f"Processing file {index}: {file}")
            if index >= len(publish_datetimes):
                logger.error(f"INDEX ERROR: index={index} >= len(datetimes)={len(publish_datetimes)}")
                continue
                
            for cookie_idx, cookie in enumerate(account_file):
                logger.debug(f"Processing cookie {cookie_idx} for file {index}")
                try:
                    logger.info(f"文件路径{str(file)}")
                    logger.info(f"视频文件名：{file}")
                    logger.info(f"标题：{title}")
                    logger.info(f"Hashtag：{tags}")
                    datetime_to_use = publish_datetimes[index] 
                    logger.info(f"Using datetime: {datetime_to_use} (index: {index})")
                    app = KSVideo(title, str(file), tags, datetime_to_use, cookie)
                    asyncio.run(app.main(), debug=False)
                except IndexError as e:
                    logger.error(f"IndexError during upload: {e}")
                    logger.error(f"Variables - index: {index}, file: {file}, dt_idx: {index}, datetimes_len: {len(publish_datetimes)}")
                    traceback.print_exc()
                except Exception as e:
                    logger.error(f"Exception in upload process: {e}")
                    traceback.print_exc()
                    
    except IndexError as e:
        logger.error(f"OUTER IndexError: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        traceback.print_exc()
    except Exception as e:
        logger.error(f"OUTER Exception: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        traceback.print_exc()

def post_video_xhs(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    logger.info("=== Starting post_video_xhs with debug logging ===")
    
    try:
        logger.info(f"Parameters: title={title}, files={files}, account_file={account_file}")
        logger.info(f"tags={tags}, category={category}, enableTimer={enableTimer}")
        logger.info(f"videos_per_day={videos_per_day}, daily_times={daily_times}, start_days={start_days}")
        
        # 生成文件的完整路径
        logger.debug("Generating file paths...")
        account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
        files = [Path(BASE_DIR / "videoFile" / file) for file in files]
        file_num = len(files)
        
        logger.info(f"Resolved account files: {[str(f) for f in account_file]}")
        logger.info(f"Resolved video files: {[str(f) for f in files]}")
        logger.info(f"File count: {file_num}")
        
        if not files:
            logger.error("ERROR: No video files provided!")
            return
            
        if not account_file:
            logger.error("ERROR: No account files provided!")
            return
        
        logger.debug(f"Generating publish datetimes for {file_num} files...")
        publish_datetimes = validate_and_generate_schedule(
            files, videos_per_day, daily_times, enableTimer, start_days, logger
        )
        
        if publish_datetimes is None:
            logger.error("Schedule generation failed - aborting upload")
            return
            
        # For XHS, we use the first datetime if multiple files
        if isinstance(publish_datetimes, list) and len(publish_datetimes) > 0:
            publish_datetime_value = publish_datetimes[0] if len(publish_datetimes) == 1 else publish_datetimes
        else:
            publish_datetime_value = 0
            
        logger.info(f"Scheduled publish times: {publish_datetime_value} (type: {type(publish_datetime_value)})")
        
        for index, file in enumerate(files):
            logger.debug(f"Processing file {index}: {file}")
            for cookie_idx, cookie in enumerate(account_file):
                logger.debug(f"Processing cookie {cookie_idx} for file {index}")
                try:
                    logger.info(f"视频文件名：{file}")
                    logger.info(f"标题：{title}")
                    logger.info(f"Hashtag：{tags}")
                    logger.info(f"Using datetime: {publish_datetime_value} for file {index}")
                    app = XiaoHongShuVideo(title, file, tags, publish_datetime_value, cookie)
                    asyncio.run(app.main(), debug=False)
                except IndexError as e:
                    logger.error(f"IndexError during upload: {e}")
                    logger.error(f"Variables - index: {index}, file: {file}")
                    traceback.print_exc()
                except Exception as e:
                    logger.error(f"Exception in upload process: {e}")
                    traceback.print_exc()
                    
    except IndexError as e:
        logger.error(f"OUTER IndexError: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        traceback.print_exc()
    except Exception as e:
        logger.error(f"OUTER Exception: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        traceback.print_exc()



# post_video("333",["demo.mp4"],"d","d")
# post_video_DouYin("333",["demo.mp4"],"d","d")