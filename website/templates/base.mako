<% import json %>
<% from website import settings %>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>OSF | ${self.title()}</title>
    % if settings.GOOGLE_SITE_VERIFICATION:
        <meta name="google-site-verification" content="${settings.GOOGLE_SITE_VERIFICATION}" />
    % endif
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="${self.description()}">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="fragment" content="!">

    % if sentry_dsn_js:
    <script src="/static/vendor/bower_components/raven-js/dist/raven.min.js"></script>
    <script src="/static/vendor/bower_components/raven-js/plugins/jquery.js"></script>
    <script>
        Raven.config('${ sentry_dsn_js }', {}).install();
    </script>
    % else:
    <script>
        window.Raven = {};
        Raven.captureMessage = function(msg, context) {
            console.error('=== Mock Raven.captureMessage called with: ===');
            console.log('Message: ' + msg);
            console.log(context);
        };
        Raven.captureException = function(err, context) {
            console.error('=== Mock Raven.captureException called with: ===');
            console.log('Error: ' + err);
            console.log(context);
        };
    </script>
    % endif

    <!-- Facebook display -->
    <meta name="og:image" content="http://centerforopenscience.org/static/img/cos_center_logo_small.png"/>
    <meta name="og:title" content="${self.title()}"/>
    <meta name="og:ttl" content="3"/>
    <meta name="og:description" content="${self.og_description()}"/>

    ${includes_top()}
    ${self.stylesheets()}
    <script src="${"/static/public/js/base-page.js" | webpack_asset}"></script>
    ${self.javascript()}

    <link href='//fonts.googleapis.com/css?family=Carrois+Gothic|Inika|Patua+One' rel='stylesheet' type='text/css'>

</head>
<body data-spy="scroll" data-target=".nav-list-spy">
    % if dev_mode:
    <style>
        #devmode {
            position:fixed;
            bottom:0;
            left:0;
            border-top-right-radius:8px;
            background-color:red;
            color:white;
            padding:.5em;
        }
    </style>
    <div id='devmode'><strong>WARNING</strong>: This site is running in development mode.</div>
    % endif

    <%include file="nav.mako"/>
     ## TODO: shouldn't always have the watermark class
    <div class="watermarked">
        <div class="container ${self.container_class()}">
            % if status:
                <%include file="alert.mako"/>
            % endif
            ${self.content()}
        </div><!-- end container -->
    </div><!-- end watermarked -->

% if not user_id:
<div id="footerSlideIn">
    <div class="container">
        <div class="row">
            <div class='col-sm-2 hidden-xs'>
                <img class="logo" src="/static/img/circle_logo.png">
            </div>
            <div class='col-sm-10 col-xs-12'>
                <a data-bind="click: dismiss" class="close" href="#">&times;</a>
                <h1>Start managing your projects on the OSF today.</h1>
                <p>Free and easy to use, the Open Science Framework supports the entire research lifecycle: planning, execution, reporting, archiving, and discovery.</p>
                <div>
                    <a data-bind="click: trackClick.bind($data, 'Create Account')" class="btn btn-primary" href="${web_url_for('index')}#signUp">Create an Account</a>

                    <a data-bind="click: trackClick.bind($data, 'Learn More')" class="btn btn-primary" href="/getting-started/">Learn More</a>
                    <a data-bind="click: dismiss">Hide this message</a>
                </div>
            </div>
        </div>
    </div>
</div>
% endif

    <%include file="footer.mako"/>
        % if settings.PINGDOM_ID:
            <script>
            var _prum = [['id', '${settings.PINGDOM_ID}'],
                            ['mark', 'firstbyte', (new Date()).getTime()]];
            (function() {
                var s = document.getElementsByTagName('script')[0]
                    , p = document.createElement('script');
                p.async = 'async';
                p.src = '//rum-static.pingdom.net/prum.min.js';
                s.parentNode.insertBefore(p, s);
            })();
            </script>
        % endif

        % if settings.GOOGLE_ANALYTICS_ID:
            <script>
            (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
            (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
            m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
            })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

            ga('create', '${settings.GOOGLE_ANALYTICS_ID}', 'auto', {'allowLinker': true});
            ga('require', 'linker');
            ga('linker:autoLink', ['centerforopenscience.org'] );
            ga('send', 'pageview');
            </script>
        % else:
            <script>
                window.ga = function(source) {
                        console.error('=== Mock ga event called: ===');
                        console.log('event: ga(' +
                                    arguments[0] + ', ' +
                                    arguments[1] + ', ' +
                                    arguments[2] + ', ' +
                                    arguments[3] + ')'
                        );
                };
          </script>
        % endif

        % if piwik_host:
            <script src="${ piwik_host }piwik.js" type="text/javascript"></script>
        % endif

        <script>
            // Mako variables accessible globally
            window.contextVars = $.extend(true, {}, window.contextVars, {
                waterbutlerURL: '${waterbutler_url if waterbutler_url.endswith('/') else waterbutler_url + '/' | js_str}',
            % if access_token:
                accessToken: '${access_token | js_str}',
            % endif
                cookieName: '${cookie_name}'
            });
        </script>

        % if piwik_host:
            <% is_public = node.get('is_public', 'ERROR') if node else True %>
            <script type="text/javascript">

                $(function() {
                    var cvars = [];
                    % if user_id:
                        cvars.push([1, "User ID", "${ user_id }", "visit"])
                        cvars.push([2, "User Name", "${ user_full_name }", "visit"])
                    % endif
                    % if node:
                        <% parent_project = parent_node.get('id') or node.get('id') %>
                        cvars.push([2, "Project ID", "${ parent_project }", "page"]);
                        cvars.push([3, "Node ID", "${ node.get('id') }", "page"]);
                        cvars.push([4, "Tags", ${ json.dumps(','.join(node.get('tags', []))) }, "page"]);
                    % endif
                    // Note: Use cookies for global site ID; only one cookie
                    // will be used, so this won't overflow uwsgi header
                    // buffer.
                    $.osf.trackPiwik("${ piwik_host }", ${ piwik_site_id }, cvars, true);
                });
            </script>
        % endif


        ${self.javascript_bottom()}
    </body>
</html>


###### Base template functions #####

<%def name="title()">
    ### The page title ###
</%def>

<%def name="container_class()">
    ### CSS classes to apply to the "content" div ###
</%def>

<%def name="description()">
    ### The page description ###
</%def>

<%def name="og_description()">
    Hosted on the Open Science Framework
</%def>

<%def name="stylesheets()">
    ### Extra css for this page. ###
</%def>

<%def name="javascript()">
    ### Additional javascript, loaded at the top of the page ###
</%def>

<%def name="content()">
    ### The body content. ###
</%def>

<%def name="javascript_bottom()">
    ### Javascript loaded at the bottom of the page ###
</%def>


<%def name="includes_top()">

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
      <script src="//cdnjs.cloudflare.com/ajax/libs/es5-shim/4.0.3/es5-shim.min.js"></script>
      <script src="//cdnjs.cloudflare.com/ajax/libs/es5-shim/4.0.3/es5-sham.min.js"></script>
    <![endif]-->

    <!-- Le styles -->
    ## TODO: Get fontawesome and select2 to play nicely with webpack
    <link rel="stylesheet" href="/static/vendor/bower_components/bootstrap/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="/static/vendor/bower_components/select2/select2.css">

    % if settings.USE_CDN_FOR_CLIENT_LIBS:
        <script src="//code.jquery.com/jquery-1.11.2.min.js"></script>
        <script>window.jQuery || document.write('<script src="/static/vendor/bower_components/jquery/dist/jquery.min.js">\x3C/script>')</script>
        <script src="//code.jquery.com/ui/1.10.3/jquery-ui.min.js"></script>
        <script>window.jQuery.ui || document.write('<script src="/static/vendor/bower_components/jquery-ui/ui/minified/jquery-ui.min.js">\x3C/script>')</script>
    % else:
        <script src="/static/vendor/bower_components/jquery/dist/jquery.min.js"></script>
        <script src="/static/vendor/bower_components/jquery-ui/ui/minified/jquery-ui.min.js"></script>
    % endif

    ## NOTE: We load vendor bundle  at the top of the page because contains
    ## the webpack runtime and a number of necessary stylesheets which should be loaded before the user sees
    ## content.
    <script src="${"/static/public/js/vendor.js" | webpack_asset}"></script>

</%def>
