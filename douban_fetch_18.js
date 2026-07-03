(function(){
var ids = ["492713108", "492712981", "492709006", "492707627", "492688752", "492681714", "492681503", "492677461", "492657287", "492655458", "492645717", "492645631", "492645365", "492645280", "492644304", "492644203", "492643977", "492640763"];
window._R2 = [];
window._D2 = false;
var i = 0;
function n() {
  if (i >= ids.length) { window._D2 = true; return; }
  var id = ids[i];
  fetch('https://www.douban.com/group/topic/' + id + '/', {credentials: 'include', cache: 'no-store'})
    .then(function(r) { return r.text(); })
    .then(function(h) {
      var p = new DOMParser();
      var d = p.parseFromString(h, 'text/html');
      var te = d.querySelector('h1');
      var ce = d.querySelector('.topic-content') || d.querySelector('#link_report');
      var c = ce ? ce.textContent.replace(/\s+/g, ' ').trim() : '';
      window._R2.push({id: id, title: (te ? te.textContent.trim() : '').slice(0, 120), content: c.slice(0, 500)});
      i++;
      setTimeout(n, 400);
    })
    .catch(function() {
      window._R2.push({id: id, title: '', content: ''});
      i++;
      setTimeout(n, 400);
    });
}
n();
return 'started ' + ids.length;
})()