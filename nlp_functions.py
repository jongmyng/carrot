# 좋아요 / 댓글
import pandas as pd
import re 

def get_like_comment():
    sample = []
    like = driver.find_elements(By.CSS_SELECTOR,
                                    'span._588sy4192._588sy41w._588sy41b2._588sy42')
    for i in like:
        sample.append(i.text)        
    sample = pd.DataFrame(sample)   
    likes = sample.iloc[0::2].reset_index(drop=True)
    comments = sample.iloc[1::2].reset_index(drop=True)
    data['like'] = likes
    data['comment'] = comments
    return data


def get_title(driver):
    posts = driver.find_elements(By.CSS_SELECTOR, 'a.click_search_result_item')
    titles = [post.get_attribute('data-title') for post in posts]
    return pd.DataFrame({"title": titles})

def get_article(driver):
    articles = driver.find_elements(By.CSS_SELECTOR, 'p._588sy4192')
    article_texts = [article.text for article in articles]
    return pd.DataFrame({"article": article_texts})

def get_etc(driver):
    dongs = driver.find_elements(By.CSS_SELECTOR,
                                 'span._588sy418w._588sy4195._588sy41w._588sy41aw._588sy41b5._588sy42')
    dong_texts = [dong.text for dong in dongs]
    etc_data = pd.DataFrame({"etc": dong_texts[0::3]}).reset_index(drop=True)  # 3개씩 중 첫 번째
    return etc_data

def get_time(driver):
    times = driver.find_elements(By.CSS_SELECTOR,
                                 'time._588sy418w._588sy4195._588sy41w._588sy41aw._588sy41b5._588sy42')
    time_texts = [time.text for time in times]
    current_time = [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * len(time_texts)
    return pd.DataFrame({"time": time_texts, "current_time": current_time})

def get_like_comment(driver):
    like_comments = driver.find_elements(By.CSS_SELECTOR, 'span._588sy4192._588sy41w._588sy41b2._588sy42')
    texts = [lc.text for lc in like_comments if '좋아요' in lc.text or '댓글' in lc.text]  # 필터링
    likes = texts[0::2]  # 좋아요
    comments = texts[1::2]  # 댓글
    return pd.DataFrame({"like": likes, "comment": comments})

def crawl(driver):
    title_data = get_title(driver)
    article_data = get_article(driver)
    etc_data = get_etc(driver)
    time_data = get_time(driver)
    like_comment_data = get_like_comment(driver)

    # DataFrame 병합
    data = pd.concat([title_data, article_data, etc_data, time_data, like_comment_data], axis=1)
    return data

def click_load_more(driver, max_clicks=2, wait_time=2):
    """
    더보기 버튼을 반복적으로 클릭하는 함수.
    """
    click_count = 0
    while click_count < max_clicks:
        try:
            more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button._876es70._876es75._876es73._588sy462._588sy4r8'))
            )
            more_button.click()
            click_count += 1
            print(f"{click_count}번째 더보기 버튼 클릭 성공")
            time.sleep(wait_time)  # 데이터 로드 대기
        except Exception as e:
            print(f"더 이상 더보기 버튼이 없거나 오류 발생: {e}")
            break


def crawl_district(driver, url, district_name, max_clicks=3):
    """
    특정 구 데이터를 크롤링하는 함수.
    """
    driver.get(url)
    time.sleep(3)

    # 더보기 버튼 클릭
    click_load_more(driver, max_clicks=max_clicks)

    # 데이터 수집
    title_data = get_title(driver)
    article_data = get_article(driver)
    etc_data = get_etc(driver)
    time_data = get_time(driver)
    like_comment_data = get_like_comment(driver)

    # 데이터 병합
    district_data = pd.concat([title_data, article_data, etc_data, time_data, like_comment_data], axis=1)
    district_data["district"] = district_name  # 구 이름 추가

    return district_data

def crawl_all_districts(driver, district_urls, max_clicks=3):
    """
    모든 구 데이터를 크롤링하는 함수.
    """
    all_data = pd.DataFrame()

    for district_name, url in district_urls.items():
        print(f"현재 구: {district_name}")
        try:
            district_data = crawl_district(driver, url, district_name, max_clicks=max_clicks)
            all_data = pd.concat([all_data, district_data], ignore_index=True)
            print(f"{district_name}: {len(district_data)}개의 데이터 수집 완료")
        except Exception as e:
            print(f"{district_name}: 크롤링 중 오류 발생 - {e}")

    return all_data


def etc_split(df):
      for idx, i in enumerate(df['etc']):
         index_ =  {idx : i.split('\n')[0]}
         category = {idx : i.split('\n')[2]}
         df.loc[idx, 'dong'] = index_.get(idx)
         df.loc[idx,'category'] = category.get(idx)
      return df

def like_comment(df):
    for idx, i in enumerate(df['like']):
        like_check = re.findall('\d+',i)
        df.loc[idx, 'like'] = like_check[0]
    for idx, i in enumerate(df['comment']):
        comment_check = re.findall('\d+',i)
        df.loc[idx, 'comment'] = comment_check[0]
    return df

def convert_time(row):
    # 문자열로 된 current_time을 datetime 객체로 변환
    current_time = datetime.strptime(row['current_time'], '%Y-%m-%d %H:%M:%S')
    time_text = row['time']

    # 정규표현식으로 "숫자"와 "단위" 추출
    match = re.search(r'(\d+)(분|시간|일)', time_text)
    if match:
        value, unit = int(match.group(1)), match.group(2)
        if unit == '분':  # 분 전
            delta = timedelta(minutes=value)
        elif unit == '시간':  # 시간 전
            delta = timedelta(hours=value)
        elif unit == '일':  # 일 전
            delta = timedelta(days=value)
        else:
            delta = timedelta(0)  # 기타 처리 없음
        update_time = current_time - delta
        return update_time.strftime('%Y-%m-%d %H:%M:%S')  # 포맷팅 후 반환
    else:
        return None  # 상대적 시간 아닌 경우

def preprocessing(df):
    etc_split(df)
    like_comment(df)  