from datetime import timedelta

from datetime import datetime
from pathlib import Path

from conf import BASE_DIR


def get_absolute_path(relative_path: str, base_dir: str = None) -> str:
    # Convert the relative path to an absolute path
    absolute_path = Path(BASE_DIR) / base_dir / relative_path
    return str(absolute_path)


def get_title_and_hashtags(filename):
    """
  获取视频标题和 hashtag

  Args:
    filename: 视频文件名

  Returns:
    视频标题和 hashtag 列表
  """

    # 获取视频标题和 hashtag txt 文件名
    txt_filename = filename.replace(".mp4", ".txt")

    # 读取 txt 文件
    with open(txt_filename, "r", encoding="utf-8") as f:
        content = f.read()

    # 获取标题和 hashtag
    splite_str = content.strip().split("\n")
    print(f"❌ ================================")
    print(f"{splite_str}")
    title = splite_str[0]
    hashtags = splite_str[1].replace("#", "").split(" ")

    return title, hashtags


import logging

logger = logging.getLogger(__name__)

def generate_schedule_time_next_day(total_videos, videos_per_day = 1, daily_times=None, timestamps=False, start_days=0):
    """
    Generate a schedule for video uploads, starting from the next day.

    Args:
    - total_videos: Total number of videos to be uploaded.
    - videos_per_day: Number of videos to be uploaded each day.
    - daily_times: Optional list of specific times of the day to publish the videos.
    - timestamps: Boolean to decide whether to return timestamps or datetime objects.
    - start_days: Start from after start_days.

    Returns:
    - A list of scheduling times for the videos, either as timestamps or datetime objects.
    """
    logger.info(f"=== generate_schedule_time_next_day called ===")
    logger.info(f"total_videos={total_videos}, videos_per_day={videos_per_day}")
    logger.info(f"daily_times={daily_times}, timestamps={timestamps}, start_days={start_days}")
    
    # Handle edge case: no videos
    if total_videos <= 0:
        logger.warning("No videos to schedule")
        return []
        
    try:
        # Validate videos_per_day
        if videos_per_day <= 0:
            logger.warning(f"videos_per_day={videos_per_day} <= 0, using 1")
            videos_per_day = 1

        if daily_times is None:
            # Default times to publish videos if not provided
            daily_times = [6, 11, 14, 16, 22]
            logger.info(f"Using default daily_times: {daily_times}")
        else:
            logger.info(f"Using provided daily_times: {daily_times}")

        logger.info(f"daily_times length: {len(daily_times)}")
        logger.info(f"videos_per_day: {videos_per_day}")
        
        # FIXED: Handle videos_per_day > len(daily_times) gracefully
        if videos_per_day > len(daily_times):
            logger.warning(f"videos_per_day={videos_per_day} > len(daily_times)={len(daily_times)}")
            logger.warning("Adjusting videos_per_day to daily_times length")
            videos_per_day = min(videos_per_day, len(daily_times))
            logger.info(f"Adjusted videos_per_day to: {videos_per_day}")

        # FIXED: Handle daily_times being empty
        if len(daily_times) == 0:
            logger.error("daily_times is empty, cannot generate schedule")
            return [0] * total_videos if total_videos > 0 else []

        # Generate timestamps
        schedule = []
        current_time = datetime.now()

        logger.info(f"Generating schedule for {total_videos} videos...")
        
        for video in range(total_videos):
            logger.debug(f"Processing video {video}/{total_videos}")
            
            day = video // videos_per_day + start_days + 1  # +1 to start from the next day
            daily_video_index = video % videos_per_day
            
            logger.debug(f"Video {video}: day={day}, daily_video_index={daily_video_index}")
            
            # FIXED: Robust index handling with bounds checking
            if daily_video_index >= len(daily_times):
                logger.warning(f"daily_video_index={daily_video_index} >= len(daily_times)={len(daily_times)}")
                # Cycle through available times
                daily_video_index = daily_video_index % len(daily_times)
                logger.warning(f"Cycled index to: {daily_video_index}")

            # Calculate the time for the current video
            hour = daily_times[daily_video_index]
            time_offset = timedelta(days=day, hours=hour - current_time.hour, minutes=-current_time.minute,
                                    seconds=-current_time.second, microseconds=-current_time.microsecond)
            timestamp = current_time + time_offset

            schedule.append(timestamp)
            logger.debug(f"Video {video}: scheduled for {timestamp}")

        logger.info(f"Generated schedule: {schedule}")
        logger.info(f"Schedule length: {len(schedule)}, expected: {total_videos}")
        
        if timestamps:
            schedule = [int(time.timestamp()) for time in schedule]
            logger.info(f"Converted to timestamps: {schedule}")
            
        return schedule
        
    except IndexError as e:
        logger.error(f"IndexError in generate_schedule_time_next_day: {e}")
        logger.error(f"Variables - total_videos: {total_videos}, videos_per_day: {videos_per_day}")
        logger.error(f"daily_times: {daily_times}, start_days: {start_days}")
        logging.exception("Full stack trace:")
        return [0] * total_videos  # FIXED: Return safe defaults instead of crashing
    except Exception as e:
        logger.error(f"Exception in generate_schedule_time_next_day: {e}")
        logging.exception("Full stack trace:")
        return [0] * total_videos  # FIXED: Return safe defaults instead of crashing
