(function(){
  var existingIds = ['492656726','492643771','492728657','492727887','492712893','492715796','492664789','492644949','492731504','492729045','492728495','492727013','492724458','492719225','492730688','492728899','492713208','492712861','492713638','492713537','492713455','492678479','492677395','492670666','492657082','492656958','492645796','492629484'];
  window._allTopics = [];
  window._topicResults = [];
  window._fetchDone = false;
  var pages = [0, 25, 50, 75, 100];
  var pageIdx = 0;

  function fetchPage() {
    if (pageIdx >= pages.length) {
      console.log('List pages done. New topics: ' + window._allTopics.length);
      fetchTopics();
      return;
    }
    var url = 'https://www.douban.com/group/shanghaizufang/discussion?start=' + pages[pageIdx];
    fetch(url, {credentials: 'include', cache: 'no-store'})
      .then(function(r) { return r.text(); })
      .then(function(html) {
        var p = new DOMParser();
        var d = p.parseFromString(html, 'text/html');
        var links = d.querySelectorAll('a[href*="/group/topic/"]');
        links.forEach(function(a) {
          var m = a.href.match(/\/topic\/(\d+)/);
          if (m && existingIds.indexOf(m[1]) < 0) {
            var t = a.textContent.replace(/\s+/g, ' ').trim();
            if (t.length > 5 && !window._allTopics.find(function(x) { return x.id === m[1]; })) {
              window._allTopics.push({id: m[1], title: t});
            }
          }
        });
        pageIdx++;
        setTimeout(fetchPage, 500);
      })
      .catch(function() { pageIdx++; setTimeout(fetchPage, 500); });
  }

  function fetchTopics() {
    var idx = 0;
    function next() {
      if (idx >= window._allTopics.length) {
        window._fetchDone = true;
        console.log('All topics fetched: ' + window._topicResults.length);
        return;
      }
      var t = window._allTopics[idx];
      fetch('https://www.douban.com/group/topic/' + t.id + '/', {credentials: 'include', cache: 'no-store'})
        .then(function(r) { return r.text(); })
        .then(function(html) {
          var p = new DOMParser();
          var d = p.parseFromString(html, 'text/html');
          var te = d.querySelector('h1');
          var title = te ? te.textContent.trim() : t.title;
          var ce = d.querySelector('.topic-content') || d.querySelector('#link_report');
          var content = ce ? ce.textContent.replace(/\s+/g, ' ').trim() : '';
          window._topicResults.push({id: t.id, title: title.slice(0, 120), content: content.slice(0, 500)});
          idx++;
          setTimeout(next, 400);
        })
        .catch(function() {
          window._topicResults.push({id: t.id, title: t.title, content: ''});
          idx++;
          setTimeout(next, 400);
        });
    }
    next();
  }

  fetchPage();
  return 'started';
})()
