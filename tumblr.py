from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import re
import os
import sys

def getXml(link):
    xml = None
    try:
        req = urllib.request.urlopen(link)
        xml = req.read().decode(req.headers.get_content_charset())
    except urllib.error.URLError as e:
        print('Error:', e.reason())
    return xml

def getImageLink(postTag):
    imageTag = postTag.find('photo-url')
    return [imageTag.text]

def getImageSetLink(postTag):
    imagesTag = postTag.find('photoset').find_all('photo')
    imagesLink = list(map(lambda x: x.find('photo-url').text, imagesTag))
    return imagesLink

def getVideoLink(postTag):
    videoTag = postTag.find('video-source')
    ext = videoTag.find('extension').text
    videoInfo = postTag.find('video-player').text
    videoId = re.findall(r'(?<=previews\\/)tumblr_.+(?=_filmstrip)', videoInfo, re.M)[0]
    return ['http://vtt.tumblr.com/%s.%s' % (videoId, ext)]

def getLink(postTag):
    if postTag.find('photoset'):
        return getImageSetLink(postTag)
    elif postTag.find('photo-url'):
        return getImageLink(postTag)
    elif postTag.find('video-source'):
        return getVideoLink(postTag)
    else:
        return None

def mkdir(name):
    path = os.getcwd() + '/' + name
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)
    return path

def download(link, path):
    data = urllib.request.urlopen(link).read()
    name = link.split('/')[-1]
    with open(path + '/' + name, 'wb') as f:
        f.write(data)

def main(user, start=0, step=50):
    apiLink = 'http://%s.tumblr.com/api/read?start=%d&num=%d'
    #user, start, step = 'username', 0, 10
    url = apiLink % (user, start, step)
    print(url)
    #soup = BeautifulSoup(open('read.xml'))
    soup = BeautifulSoup(getXml(url))
    posts = soup.find_all('post')
    path = mkdir(user)
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


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 1:
        print('<username> [start] [step]')
    elif len(args) == 1:
        main(args[0])
    elif len(args) == 2:
        main(args[0], args[1])
    else:
        main(args[0], args[1], args[2])
