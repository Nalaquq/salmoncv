var scv = {
  get: function(url, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url);
    xhr.onload = function() {
      if (xhr.status === 200) {
        try { cb(JSON.parse(xhr.responseText)); } catch(e) {}
      }
    };
    xhr.send();
  },

  post: function(url, body, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
      try { cb(JSON.parse(xhr.responseText)); } catch(e) {}
    };
    xhr.send(JSON.stringify(body));
  },

  text: function(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val;
  },

  badge: function(id, on) {
    var el = document.getElementById(id);
    if (el) {
      el.className = 'badge ' + (on ? 'badge-on' : 'badge-off');
    }
  }
};

document.addEventListener('DOMContentLoaded', function() {
  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  if (toggle && links) {
    toggle.addEventListener('click', function() {
      links.classList.toggle('open');
    });
  }
});
