from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import argparse
import re
import os

# 获取link返回的xml代码
def getXml(link):
    xml = None
    try:
        req = urllib.request.urlopen(link)
        xml = req.read().decode(req.headers.get_content_charset())
    except urllib.error.HTTPError as e:
        print('Error:', e.reason())
    return xml

# 得到post的总数，因为api所限，每次最多获取50个post
def getTotalPost(xmlCode):
    #total = re.findall(r'(?<=<posts )(\w|"|\d)(?=">)', xmlCode)[0]
    total = re.findall(r'(?<= total=")\d+(?=">)', xmlCode, re.M)[0]
    return int(total)

# 传入photo-url结点，得到图片url
def getImageLink(photoUrlTag):
    return [photoUrlTag.text]

# 图片集post中有多个photo子结点，把每个photo子结点看作图片post处理
def getImageSetLink(photoSetTag):
    imagesTag = photoSetTag.find_all('photo')
    imagesLink = list(map(lambda x: x.find('photo-url').text, imagesTag))
    return imagesLink

# 视频post中有两个子结点，从videoSourceTag中获取视频格式，videoPlayerTag获取视频编号，拼接出url
def getVideoLink(videoSourceTag, videoPlayerTag):
    #videoTag = postTag.find('video-source')
    ext = videoSourceTag.find('extension').text
    videoText = videoPlayerTag.text
    videoId = re.findall(r'(?<=previews\\/)tumblr_.+(?=_filmstrip)', videoText, re.M)[0]
    return ['http://vtt.tumblr.com/%s.%s' % (videoId, ext)]

# 判断post的类型，进行不同的处理，else块中包括纯文字post
def getLink(postTag):
    photoSetTag = postTag.find('photoset')
    photoUrlTag = postTag.find('photo-url')
    videoSourceTag = postTag.find('video-source')
    videoPlayerTag = postTag.find('video-player')

    if photoSetTag:
        return getImageSetLink(photoSetTag)
    elif photoUrlTag:
        return getImageLink(photoUrlTag)
    elif videoSourceTag:
        return getVideoLink(videoSourceTag, videoPlayerTag)
    else:
        return None

# 通过用户名创建文件夹，用来存放已下载的资源
def mkdir(name):
    path = os.getcwd() + '/' + name
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)
    return path

# 将资源保存到文件
def download(link, path):
    try:
        data = urllib.request.urlopen(link).read()
        name = link.split('/')[-1]
        with open(path + '/' + name, 'wb') as f:
            f.write(data)
    except urllib.error.HTTPError as e:
        print('Download Error')

# 读取link中的xml代码，遍历post结点，下载post中的资源
def downloadPost(xmlLink, path):
    soup = BeautifulSoup(getXml(xmlLink))
    posts = soup.find_all('post')
    print('post count: ', len(posts))
    postCount, subImgCount = 0, 0
    for post in posts:
        links = getLink(post)
        if links:
            for link in links:
                print('Downloading:', postCount, subImgCount, link)
                download(link, path)
                subImgCount += 1
        postCount += 1
        subImgCount = 0

def main(user, postids=None, start=None, step=None):
    apiLink = 'http://%s.tumblr.com/api/read?' % user
    path = mkdir(user)
    if postids:#
        for postid in postids:
            args = 'id=%s' % postid
            print(apiLink + args)
            downloadPost(apiLink + args, path)
    else:
        total = step if step else getTotalPost(getXml(apiLink))
        cur = start if start else 0
        while total > 0:
            if total >= 50:
                args = 'start=%d&num=50' % cur
                print(apiLink + args)
                downloadPost(apiLink + args, path)
                total -= 50
                cur += 50
            else:
                args = '&start=%d&num=%d' % (cur, total)
                print(apiLink + args)
                downloadPost(apiLink + args, path)
                total = 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser('tumblr.py')
    parser.add_argument('-u', '--username', help='Tumblr用户名', required=True)
    parser.add_argument('-p', '--post', help='指定post编号', nargs='+')
    parser.add_argument('-s', '--start', help='起始位置')
    parser.add_argument('-n', '--num', help='抓取个数，最多不超过50')
    args = vars(parser.parse_args())
    if args['post']:
        main(args['username'], args['post'])
    else:
        main(args['username'], start=args['start'], step=args['num'])
