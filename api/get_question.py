import tqdm
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from multiprocessing import Pool, cpu_count

from database.SQLighter import SQLighter

CHROMEDRIVER = '/Users/leonid/.wdm/chromedriver/2.46/mac64/chromedriver'
DATABASE_NAME = '../database/tasks.db'


def get_task(driver):
    driver.get('https://xn----8sbhebeda0a3c5a7a.xn--p1ai/%D1%82%D0%B5%D1%81%D1%82/')
    content = driver.find_element_by_class_name('content')
    word = content.find_element_by_class_name('text').text.split()[-1][:-1]
    first_option, second_option = map(lambda x: x.text, content.find_elements_by_class_name("button"))

    content.find_element_by_class_name('button').click()
    content = driver.find_element_by_class_name('col-sm-8')

    try:
        content.find_element_by_css_selector('.rule.correct')
        answer = 0

    except Exception as e:
        answer = 1

    return word, first_option, second_option, answer


def get_n_tasks(n):
    db_worker = SQLighter(DATABASE_NAME)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(CHROMEDRIVER, chrome_options=chrome_options)
    tasks = []

    pbar = tqdm.tqdm(total=n)

    for i in range(n):
        try:
            task = get_task(driver)
        except Exception:
            print('Passed error!')
            pbar.update(1)
            continue

        tasks.append(task)

        pbar.update(1)
        pbar.set_description("Parsing tasks ...")

    all_tasks = db_worker.select_all()
    for task in tasks:
        if task not in all_tasks:
            db_worker.add_task(*task)

    db_worker.close()


def main():
    get_n_tasks(1000)


if __name__ == '__main__':
    main()
