<div class="osf-nav-wrapper">

<nav class="navbar navbar-inverse navbar-fixed-top" id="navbarScope" role="navigation">
    <div class="container">
    <div class="navbar-header">
      <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
        <span class="sr-only">Toggle navigation</span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>
      <a class="navbar-brand hidden-sm hidden-xs" href="/"><img src="/static/img/cos-white2.png" class="osf-navbar-logo" width="27" alt="COS logo"/> Open Science Framework</a>
      <a class="navbar-brand visible-sm visible-xs" href="/"><img src="/static/img/cos-white2.png" class="osf-navbar-logo" width="27" alt="COS logo"/> OSF</a>
    </div>
    <div id="navbar" class="navbar-collapse collapse navbar-right">
      <ul class="nav navbar-nav">
        % if user_name:
            <li><a href="/dashboard/">My Dashboard</a></li>
        % else:
            <li><a href="/explore/activity/">Browse New Projects</a></li>
        % endif
        <li class="dropdown">
          <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">Explore <span class="caret hidden-xs"></span></a>
          <ul class="dropdown-menu" role="menu">
              <li><a href="/search/?q=*&amp;filter=registration">Registry</a></li>
              <li><a href="/meetings/">Meetings</a></li>
          </ul>
        </li>
        <li class="dropdown">
          <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">Help <span class="caret hidden-xs"></span></a>
          <ul class="dropdown-menu" role="menu">
              <li><a href="/4znZP/wiki/home">About</a></li>
              <li><a href="/faq/">FAQ</a></li>
              <li><a href="/getting-started">Getting Started</a></li>
              <li><script type="text/javascript">document.write("<n uers=\"znvygb:fhccbeg@bfs.vb\" ery=\"absbyybj\">Rznvy Fhccbeg</n>".replace(/[a-zA-Z]/g,function(e){return String.fromCharCode((e<="Z"?90:122)>=(e=e.charCodeAt(0)+13)?e:e-26)}));</script><noscript>Email Support: <span class="obfuscated-email-noscript"><strong><u>supp<span style="display:none;">null</span>ort@<span style="display:none;">null</span>osf.<span style="display:none;">null</span>io</u></strong></span></noscript></li>
                <li><script type="text/javascript">document.write("<n uers=\"znvygb:pbagnpg@bfs.vb\" ery=\"absbyybj\">Pbagnpg</n>".replace(/[a-zA-Z]/g,function(e){return String.fromCharCode((e<="Z"?90:122)>=(e=e.charCodeAt(0)+13)?e:e-26)}));</script><noscript>Contact OSF: <span class="obfuscated-email-noscript"><strong><u>cont<span style="display:none;">null</span>act@<span style="display:none;">null</span>osf.<span style="display:none;">null</span>io</u></strong></span></noscript></li>
          </ul>
        </li>

        <!-- ko ifnot: onSearchPage -->
        <li class="hidden-xs" data-bind="click : toggleSearch, css: searchCSS">
            <a class="" >
                <span rel="tooltip" data-placement="bottom" title="Search OSF" class="fa fa-search fa-lg" ></span>
            </a>
        </li>
        <!-- /ko -->
        % if user_name and display_name:
        <li>
            <a class="hidden-lg hidden-xs nav-profile" href="/profile/">
                <span rel="tooltip" data-placement="bottom" title="${user_name}" class="osf-gravatar"><img src="${user_gravatar}" alt="User gravatar"/> </span>
            </a>
            <a class="visible-lg visible-xs nav-profile" href="/profile/">
                <span rel="tooltip" data-placement="bottom" title="${user_name}"><span class="osf-gravatar"> <img src="${user_gravatar}" alt="User gravatar"/> </span> ${display_name}</span>
            </a>
        </li>
        <li>
            <a href="${web_url_for('user_profile')}">
                <span rel="tooltip" data-placement="bottom" title="Settings" class="fa fa-cog hidden-xs fa-lg"></span>
                <span class="visible-xs">Settings</span>
            </a>
        </li>
        <li>
            <a href="${web_url_for('auth_logout')}">
                <span rel="tooltip" data-placement="bottom" title="Log&nbsp;out" class="fa fa-sign-out hidden-xs fa-lg"></span>
                <span class="visible-xs">Log out</span>
            </a>
        </li>
        % elif allow_login:
        <li class="dropdown sign-in" data-bind="with: $root.signIn">
          <div class="btn-group">
            <button type="button" class="btn btn-info btn-top-login dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
              Sign in <span class="caret hidden-xs"></span>
            </button>
            <ul class="dropdown-menu" id="menuLogin" role="menu">
              <form class="form" id="signInForm" data-bind="submit: submit" action="${login_url}" method="POST">
                  <div class="form-group"><input id="email" class="form-control" type="email" data-bind="value: username" name="username" placeholder="Email" aria-label="Username"></div>
                  <div class="form-group"><input name="password" id="password" class="form-control" type="password" placeholder="Password" data-bind="value: password" aria-label="Password"></div>
                  <div class="form-group"><button type="submit" id="btnLogin" class="btn btn-block btn-primary">Login</button></div>
                 <div class="text-center m-b-sm"> <a href="/forgotpassword/">Forgot Password?</a></div>
               </form>
            </ul>
          </div>
        </li>
        % endif
    </div><!--/.navbar-collapse -->
    </div>


</nav>
    <!-- ko ifnot: onSearchPage -->
        <%include file='./search_bar.mako' />
    <!-- /ko -->
</div>
