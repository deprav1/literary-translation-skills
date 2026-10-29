import json,urllib.request,urllib.parse
from bs4 import BeautifulSoup
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'site/research'
def getps(u):
    s=BeautifulSoup(urllib.request.urlopen(urllib.request.Request(urllib.parse.quote(u,safe=':/_%()?=;'),headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read(),'html.parser')
    return [' '.join(x.get_text(' ',strip=True).split()) for x in s.select('.mw-parser-output p') if len(x.get_text(strip=True))>20]
en=getps('https://en.wikisource.org/wiki/Mystery_Tales_of_Edgar_Allan_Poe/The_Tell-Tale_Heart')[1:]
ru=getps('https://ru.wikisource.org/wiki/Сердце-изобличитель_(По;_Бальмонт)');assert len(en)==len(ru)==18
c=[]
for idx in [1,2,3,4,6,8,10,11,12,13,14,15,16,17]:
    c.append({'id':f'poe-extra-{idx:02d}','source_text':en[idx],'human_text':ru[idx],'author':'Эдгар Аллан По','title':'The Tell-Tale Heart / Сердце-изобличитель','translator':'Константин Бальмонт','published':'1843 (original); 1913 (translation edition)','source_url':'https://en.wikisource.org/wiki/Mystery_Tales_of_Edgar_Allan_Poe/The_Tell-Tale_Heart','human_url':'https://ru.wikisource.org/wiki/Сердце-изобличитель_(По;_Бальмонт)','rights_basis':'Original 1843; author died 1849. Translation edition 1913; translator died 1942. Wikisource marks the editions public domain under the stated jurisdictional notice.','adaptation':'Verbatim digital transcription; whitespace normalized.','tag':'нервная проза'})
s=BeautifulSoup(urllib.request.urlopen(urllib.request.Request('https://www.gutenberg.org/files/774/774-h/774-h.htm',headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read(),'html.parser');h=next(h for h in s.find_all(['h1','h2','h3','h4']) if 'Doer of Good' in h.get_text());wp=[]
for e in h.find_all_next('p'):
    t=' '.join(e.get_text(' ',strip=True).split())
    if len(t)>20:wp.append(t)
human=['Была ночь, и Он был один.','И Он увидел вдали стены круглого города, и направился к этому городу.','И когда Он прошел через зал из халцедона и через зал из яшмы, и пришел в длинный пиршественный зал, Он увидел на пурпурном ложе человека, чьи волосы были увенчаны алыми розами и чьи губы были красны от вина.','И Он подошел к нему сзади, дотронулся до плеча его, и сказал: — Почему ты живешь так?','И юноша обернулся и узнал Его, и сказал в ответ: — Но ведь когда-то я был прокаженным, и Ты исцелил меня. Как же мне иначе жить.','И Он оставил дом этот и вышел снова на улицу.','И вскоре Он увидал женщину, чье лицо и одежда были разрисованы, и ноги которой были обуты в жемчуг.','Лицо женщины было подобно прекрасному лику идола, а глаза юноши горели сладострастием.','И Он быстро пошел за ними и коснулся руки юноши и сказал. — Почему ты смотришь на эту женщину и еще таким взором?','И юноша обернулся и узнал Его, и сказал: — Но ведь когда-то я был слепым и Ты вернул мне зрение. На что же другое мне смотреть?','И Он догнал женщину и коснулся разрисованной одежды ее и сказал ей: — Разве нет иного пути, кроме пути греха?','И женщина обернулась и узнала Его, засмеялась, и сказала: — Но ты отпустил мне грехи мои, и путь этот — веселый путь.']
assert len(wp)>=14
for j,idx in enumerate([1,2,4,5,6,7,8,9,10,11,12,13]):
    c.append({'id':f'wilde-extra-{j+1:02d}','source_text':wp[idx],'human_text':human[j],'author':'Оскар Уайльд','title':'The Doer of Good / Творитель добра','translator':'Михаил Фёдорович Ликиардопуло','published':'1894 (original); 1911 (translation, Новый чтец-декламатор, Kyiv, p.61)','source_url':'https://www.gutenberg.org/files/774/774-h/774-h.htm','human_url':'https://ru.wikisource.org/wiki/Творитель_добра_(Уайльд)','rights_basis':'Original 1894; Wilde died 1900. Translation publication 1911; translator died 1925. Wikisource provides the historical attribution and public-domain notice for the cited edition.','adaptation':'Verbatim source transcription with normalized whitespace; sentence-group fragment boundaries preserve the matched historical sequence.','tag':'притча и диалог'})
assert len(c)==26
(R/'corpus_candidates.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8');print('candidates',len(c))
