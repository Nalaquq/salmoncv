var scv = {
  get: function(url, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url);
    xhr.timeout = 8000;
    xhr.onload = function() {
      if (xhr.status === 200) {
        try { cb(JSON.parse(xhr.responseText)); } catch(e) {}
      }
    };
    xhr.onerror = function() {};
    xhr.ontimeout = function() {};
    xhr.send();
  },

  post: function(url, body, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url);
    xhr.timeout = 15000;
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
      try { cb(JSON.parse(xhr.responseText)); } catch(e) {}
    };
    xhr.onerror = function() {};
    xhr.ontimeout = function() {};
    xhr.send(JSON.stringify(body));
  },

  text: function(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val;
  },

  // state: true/false for on/off, or the string 'warn' for a cautionary badge
  // (e.g. process alive but not actually producing output).
  badge: function(id, state) {
    var el = document.getElementById(id);
    if (el) {
      var cls = state === 'warn' ? 'badge-warn' : (state ? 'badge-on' : 'badge-off');
      el.className = 'badge ' + cls;
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
