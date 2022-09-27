# using asynchronous HTTP requests, download, organise, and store all images and titles for the webcomic "acception".
# webtoon.com's only protection is requiring that the Referer header be from their domain, and a bit of rate limiting.
# I later built a simple PHP page hosted on an apache server on my laptop to read all of them on my phone.

from bs4 import BeautifulSoup
import os
os.chdir(r"C:\Apache24\htdocs\reader\acceptionImg")
import aiohttp
import asyncio
n=209 # number of episodes to download
urls=[f"https://www.webtoons.com/en/drama/acception/episode-1/viewer?title_no=1513&episode_no={i}"for i in range(1,n+1)]
referer="https://www.webtoons.com/en/drama/acception/episode-1/viewer"

#async def dlParseDl
#no, find all image urls (+titles) first then batch download
async def dlappend(session, url):
    async with session.get(url, timeout=0) as response:
        return await response.text()

#download srcs[i] to episode{episode}/img{index}.png
async def dlsave(session, url, episode, index):
    for i in range(10):
        try:
            async with session.get(url, timeout=0, headers={"Referer":referer}) as response:
                if not os.path.exists(f"episode{episode}"):
                    os.mkdir(f"episode{episode}")
                with open(fr"episode{episode}\img{index}.jpg", mode='wb') as f:
                    f.write(await response.read())
            break
        except aiohttp.ServerDisconnectedError:
            pass

from dataclasses import dataclass
from typing import List
@dataclass
class Page:
    name: str
    imgs: List[str]

async def rfunc(): #main, kinda
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(force_close=True)) as session:
        pages = await asyncio.gather(*[dlappend(session, url) for url in urls])
        print("whole page downloads done")
        #get image urls and titles with bs4
        savedPages=[]
        for page in pages:
            soup=BeautifulSoup(page, 'html.parser')
            savedPages.append(Page(
                #title
                soup.find("h1",attrs={"class":"subj_episode"}).contents[0].string.replace("&#39;","'"),
                #images
                [image['data-url'] for image in soup.find_all("img",attrs={"class":"_images"})]
            ))
        with open(r"..\acceptionNames.txt",'w') as f:
            f.write('\n'.join(savedPage.name for savedPage in savedPages))
        print("parsing done, names saved")
        lst=[]
        i=1
        for savedPage in savedPages:
            j=1
            for img in savedPage.imgs:
                lst.append(dlsave(session, img, i, j))
                j+=1
            i+=1
                
        await asyncio.gather(*lst)

#apparently should replace these two lines with asyncio.run(rfunc()) to get rid of warning
loop = asyncio.get_event_loop()
loop.run_until_complete(rfunc())
print("all done")
