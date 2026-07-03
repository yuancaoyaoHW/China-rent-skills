
(function() {
  var topics = [{"id": "492731504", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c\u4e1c\u65b9\u4f53\u80b2\u4e2d\u5fc3\u9644\u8fd1 8\u53f7\u7ebf\u51cc\u5146\u65b0\u6751 \u6574\u79df\u4e24"}, {"id": "492729045", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c\u4e0a\u6d77\u623f\u4e1c\u76f4\u79df 2/6/7/9/11/12/13\u53f7\u7ebf"}, {"id": "492728657", "title": "\u623f\u4e1c\u76f4\u79df\uff012K+ \u65e0\u4e2d\u4ecb\u8d39 /\u76f4\u8fbe\u5f20\u6c5f\u3001\u524d\u6ee9/\u4e00\u5ba4\u6237\u72ec\u53a8"}, {"id": "492728495", "title": "\u4e0a\u6d77\u5e02\u533a\uff5c6/12\u53f7\u7ebf\u5de8\u5cf0\u8def \u4e00\u5ba4\u62372500"}, {"id": "492727013", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c12\u53f7\u7ebf\u5de8\u5cf0\u8def \u6bd5\u4e1a\u5b63\u6c34\u7535"}, {"id": "492724458", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c\u4e16\u7eaa\u516c\u56ed \u4e00\u5ba4\u4e00\u53856000"}, {"id": "492719225", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c\u4e16\u535a\uff5c\u4e1c\u660e\u8def\u4e24\u623f\u4e00\u5385"}, {"id": "492730688", "title": "\u623f\u4e1c\u81ea\u5df1\u7684\u623f\u5b50\u51fa\u79df \u72ec\u53a8\u72ec\u536b\u4e00\u5ba4\u6237 29\u5e73 1290"}, {"id": "492728899", "title": "\u5b9d\u5c71\u5609\u5b9a\uff5c\u9759\u5b89\u4e00\u53f7\u7ebf\u6c76\u6c34\u8def \u6c11\u6c34\u6c11\u7535"}, {"id": "492727887", "title": "\u6025\u8f6c\u79df\uff01\u6768\u601d\u8def\u601d\u6d66\u5c0f\u533a 2200\u5143\u7cbe\u88c5\u4e00\u5ba4\u6237"}, {"id": "492713208", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c8\u53f7\u7ebf\u6768\u601d \u62bc\u4e00\u4ed8\u4e003000"}, {"id": "492712893", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c\u6574\u79df\uff01\u4e16\u7eaa\u5927\u90532.4.6.9 \u4e00\u5ba4\u62372800"}, {"id": "492712861", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c8\u53f7\u7ebf\u6574\u79df\u4e00\u5c45\u5ba4 \u6c5f\u6708\u8def\u8054\u822a\u8def"}, {"id": "492715796", "title": "\u6d66\u4e1c\u5185\u73af\u6d0b\u6cfe\u76f4\u79df"}, {"id": "492713638", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c\u6d66\u4e1c\u79df\u623f6-10\u53f7\u7ebf\u53cc\u6c5f\u8def\u9644\u8fd1 \u9ad8\u6865"}, {"id": "492713537", "title": "\u6d66\u4e1c 6/9/10/12\u53f7\u7ebf\u79df\u623f \u65e0\u4e2d\u4ecb\u8d39"}, {"id": "492713455", "title": "\u6d66\u4e1c\u79df\u623f 6-8-11\u53f7\u7ebf\u4e1c\u65b9\u4f53\u80b2\u4e2d\u5fc3\u9644\u8fd1"}, {"id": "492678479", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c\u4e1c\u65b9\u4f53\u80b2\u4e2d\u5fc3\u79df\u623f 6/8/11\u53f7\u7ebf"}, {"id": "492677395", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c6\u53f7\u7ebf\u4e1c\u9756\u8def \u671d\u5357\u4e00"}, {"id": "492670666", "title": "\u6d66\u4e1c 6-8-11\u53f7\u7ebf\u4e1c\u65b9\u4f53\u80b2\u4e2d\u5fc3\u7ad9 \u671d\u5357\u5e26\u9633\u53f0"}, {"id": "492664789", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c\u9f99\u9633\u8def\u9644\u8fd1\u6b21\u5367 2/7/16/18\u53f7\u7ebf \u9650\u7537\u751f"}, {"id": "492657082", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c\u6574\u79df12\u53f7\u7ebf\u91d1\u4eac\u8def \u5de8\u5cf0\u8def"}, {"id": "492656958", "title": "13/18\u53f7\u7ebf \u83b2\u6eaa\u8def\u3001\u5317\u8521\u3001\u9648\u6625\u8def \u6c34\u7535\u5168\u514d"}, {"id": "492645796", "title": "11/18\u53f7\u7ebf \u5fa1\u6865\u3001\u79c0\u6cbf\u8def\u3001\u5eb7\u6865 \u6c34\u7535\u5168\u514d"}, {"id": "492644949", "title": "\u6d66\u4e1c\u65b0\u533a\uff5c11\u53f7\u7ebf\u4e09\u6797\u5c0f\u4e00\u5c45\u5ba43200"}, {"id": "492629484", "title": "\u6d66\u4e1c \u5fa1\u6865\u79df\u623f"}];
  var results = [];
  var idx = 0;
  
  function fetchNext() {
    if (idx >= topics.length) {
      window._doubanResults = results;
      console.log('DONE: ' + results.length + ' topics extracted');
      console.log(JSON.stringify(results));
      return;
    }
    var t = topics[idx];
    var url = 'https://www.douban.com/group/topic/' + t.id + '/';
    fetch(url, {credentials: 'include', cache: 'no-store'})
      .then(function(r) { return r.text(); })
      .then(function(html) {
        var parser = new DOMParser();
        var doc = parser.parseFromString(html, 'text/html');
        var titleEl = doc.querySelector('h1');
        var title = titleEl ? titleEl.textContent.trim() : t.title;
        // 正文在 div.topic-content 或 #link_report
        var contentEl = doc.querySelector('.topic-content') || doc.querySelector('#link_report') || doc.querySelector('.rich-content');
        var content = contentEl ? contentEl.textContent.replace(/\s+/g, ' ').trim() : '';
        var authorEl = doc.querySelector('.from-author a') || doc.querySelector('h3 a');
        var author = authorEl ? authorEl.textContent.trim() : '';
        var timeEl = doc.querySelector('.create-time');
        var time = timeEl ? timeEl.textContent.trim() : '';
        
        if (content.length > 20) {
          results.push({id: t.id, url: url, title: title, content: content.slice(0, 800), author: author, time: time});
          console.log('OK ' + (idx+1) + '/' + topics.length + ': ' + title.slice(0,40));
        } else {
          results.push({id: t.id, url: url, title: title, content: '', author: author, time: time});
          console.log('EMPTY ' + (idx+1) + '/' + topics.length + ': ' + title.slice(0,40));
        }
        idx++;
        setTimeout(fetchNext, 800);
      })
      .catch(function(e) {
        results.push({id: t.id, url: url, title: t.title, content: 'FETCH_ERROR: ' + e, author: '', time: ''});
        console.log('ERR ' + (idx+1) + ': ' + t.id + ' ' + e);
        idx++;
        setTimeout(fetchNext, 800);
      });
  }
  
  window._doubanResults = [];
  fetchNext();
  return 'started fetching ' + topics.length + ' topics';
})()
