<%inherit file="base.mako"/>
<%def name="title()">Search</%def>
<%def name="content()">
    <div id="searchControls" class="scripted">
        <%include file='./search_bar.mako' />
        <div class="row">
            <div class="col-md-12">
                <div class="row m-t-md">
                    <!-- ko if: categories().length > 0-->
                    <div class="col-md-3">
                        <div class="row">
                            <div class="col-md-12">
                                <ul class="nav nav-pills nav-stacked" data-bind="foreach: categories">

                                    <!-- ko if: $parent.category().name === name -->
                                            <li class="active">
                                                <a data-bind="click: $parent.filter.bind($data)">{{ display }}<span class="badge pull-right">{{count}}</span></a>
                                            </li>
                                        <!-- /ko -->
                                        <!-- ko if: $parent.category().name !== name -->
                                            <li>
                                                <a data-bind="click: $parent.filter.bind($data)">{{ display }}<span class="badge pull-right">{{count}}</span></a>
                                            </li>
                                        <!-- /ko -->

                                </ul>
                            </div>
                        </div>
                        <!-- ko if: tags().length -->
                        <div class="row">
                            <div class="col-md-12">
                                <h4> Improve your search:</h4>
                                <span class="tag-cloud" data-bind="foreach: tags">
                                    <!-- ko if: count === $parent.tagMaxCount() && count > $parent.tagMaxCount()/2  -->
                                    <span class="cloud-tag tag-big pointer tag-container"
                                          data-bind="click: $root.clickTag.bind($parentContext, name, 'add')">
                                        <span class="cloud-text">
                                            {{name}}
                                        </span>
                                        <i class="fa fa-times-circle remove-tag big"
                                           data-bind="click: $root.clickTag.bind($parentContext, name, 'remove')"></i>
                                    </span>
                                    <!-- /ko -->
                                    <!-- ko if: count < $parent.tagMaxCount() && count > $parent.tagMaxCount()/2 -->
                                    <span class="cloud-tag tag-med pointer tag-container"
                                          data-bind="click: $root.clickTag.bind($parentContext, name, 'add')">
                                        <span class="cloud-text">
                                            {{name}}
                                        </span>
                                        <i class="fa fa-times-circle remove-tag med"
                                           data-bind="click: $root.clickTag.bind($parentContext, name, 'remove')"></i>
                                    </span>
                                    <!-- /ko -->
                                    <!-- ko if: count <= $parent.tagMaxCount()/2-->
                                    <span class="cloud-tag tag-sm pointer tag-container"
                                          data-bind="click: $root.clickTag.bind($parentContext, name, 'add')">
                                        <span class="cloud-text">
                                            {{name}}
                                        </span>
                                        <i class="fa fa-times-circle remove-tag"
                                           data-bind="click: $root.clickTag.bind($parentContext, name, 'remove')"></i>
                                    </span>
                                    <!-- /ko -->
                                </span>
                            </div>
                        </div>
                        <br />
                        <!-- /ko -->
                    </div>
                    <!-- /ko -->
                    <div class="col-md-9">
                        <!-- ko if: searchStarted() && !totalCount() -->
                        <div class="search-results hidden" data-bind="css: {hidden: totalCount() }">No results found.</div>
                        <!-- /ko -->
                        <!-- ko if: totalCount() -->
                        <div data-bind="foreach: results">
                            <div class="search-result" data-bind="template: { name: category, data: $data}"></div>
                        </div>
                        <ul class="pager">
                            <li data-bind="css: {disabled: !prevPageExists()}">
                                <a href="#" data-bind="click: pagePrev">Previous Page </a>
                            </li>
                            <span data-bind="visible: totalPages() > 0">
                                <span data-bind="text: navLocation"></span>
                            </span>
                            <li data-bind="css: {disabled: !nextPageExists()}">
                                <a href="#" data-bind="click: pageNext"> Next Page</a>
                            </li>

                        </ul>
                        <!-- /ko -->


                        <div class="buffer"></div>
                    </div><!--col-->
                </div><!--row-->
            </div><!--col-->
        </div><!--row-->
    </div>

    <script type="text/html" id="SHARE">
        <!-- ko if: $data.links -->
            <h4><a data-bind="attr.href: links[0].url">{{ title }}</a></h4>
        <!-- /ko -->

        <!-- ko ifnot: $data.links -->
            <h4><a data-bind="attr.href: id.url">{{ title }}</a></h4>
        <!-- /ko -->

        <h5>Description: <small>{{ description | default:"No Description" | fit:500}}</small></h5>

        <!-- ko if: contributors.length > 0 -->
        <h5>
            Contributors: <small data-bind="foreach: contributors">
                <span>{{ $data.given + " " + $data.family}}</span>
            <!-- ko if: ($index()+1) < ($parent.contributors.length) -->&nbsp;- <!-- /ko -->
            </small>
        </h5>
        <!-- /ko -->

        <!-- ko if: $data.source -->
        <h5>Source: <small>{{ source }}</small></h5>
        <!-- /ko -->

        <!-- ko if: $data.isResource -->
        <button class="btn btn-primary pull-right" data-bind="click: $parents[1].claim.bind($data, _id)">Curate This</button>
        <br>
        <!-- /ko -->
    </script>
    <script type="text/html" id="user">

        <div class="row">
            <div class="col-md-2">
                <img class="social-gravatar" data-bind="visible: gravatarUrl(), attr.src: gravatarUrl()">
            </div>
            <div class="col-md-10">
                <h4><a data-bind="attr.href: url"><span>{{ user }}</span></a></h4>
                <p>
                    <span data-bind="visible: job_title, text: job_title"></span><!-- ko if: job_title && job --> at <!-- /ko -->
                    <span data-bind="visible: job, text: job"></span><!-- ko if: job_title || job --><br /><!-- /ko -->
                    <span data-bind="visible: degree, text: degree"></span><!-- ko if: degree && school --> from <!-- /ko -->
                    <span data-bind="visible: school, text: school"></span><!-- ko if: degree || school --><br /><!-- /ko -->
                </p>
                <!-- ko if: social -->
                <ul class="list-inline">
                    <li data-bind="visible: social.personal">
                        <a data-bind="attr.href: social.personal">
                            <i class="fa fa-globe social-icons" data-toggle="tooltip" title="Personal Website"></i>
                        </a>
                    </li>

                    <li data-bind="visible: social.twitter">
                        <a data-bind="attr.href: social.twitter">
                            <i class="fa fa-twitter social-icons" data-toggle="tooltip" title="Twitter"></i>
                        </a>
                    </li>
                    <li data-bind="visible: social.github">
                        <a data-bind="attr.href: social.github">
                            <i class="fa fa-github-alt social-icons" data-toggle="tooltip" title="Github"></i>
                        </a>
                    </li>
                    <li data-bind="visible: social.linkedIn">
                        <a data-bind="attr.href: social.linkedIn">
                            <i class="fa fa-linkedin social-icons" data-toggle="tooltip" title="LinkedIn"></i>
                        </a>
                    </li>
                    <li data-bind="visible: social.scholar">
                        <a data-bind="attr.href: social.scholar">
                            <img class="social-icons" src="/static/img/googlescholar.png"data-toggle="tooltip" title="Google Scholar">
                        </a>
                    </li>
                    <li data-bind="visible: social.impactStory">
                        <a data-bind="attr.href: social.impactStory">
                            <i class="fa fa-info-circle social-icons" data-toggle="tooltip" title="ImpactStory"></i>
                        </a>
                    </li>
                    <li data-bind="visible: social.orcid">
                        <a data-bind="attr.href: social.orcid">
                            <i class="fa social-icons" data-toggle="tooltip" title="ORCiD">iD</i>
                        </a>
                    </li>
                    <li data-bind="visible: social.researcherId">
                        <a data-bind="attr.href: social.researcherId">
                            <i class="fa social-icons" data-toggle="tooltip" title="ResearcherID">R</i>
                        </a>
                    </li>
                </ul>
                <!-- /ko -->
            </div>
        </div>

    </script>
    <script type="text/html" id="node">
      <!-- ko if: parent_url -->
      <h4><a data-bind="attr.href: parent_url">{{ parent_title}}</a> / <a data-bind="attr.href: url">{{title }}</a></h4>
        <!-- /ko -->
        <!-- ko if: !parent_url -->        
        <h4><span data-bind="if: parent_title">{{ parent_title }} /</span> <a data-bind="attr.href: url">{{title }}</a></h4>
        <!-- /ko -->

        <p data-bind="visible: description"><strong>Description:</strong> {{ description | fit:500 }}</p>

        <!-- ko if: contributors.length > 0 -->
        <p>
            <strong>Contributors:</strong> <span data-bind="foreach: contributors">
                <!-- ko if: url -->
                    <a data-bind="attr.href: url">{{ fullname }}</a>
                <!-- /ko-->
                <!-- ko ifnot: url -->
                    {{ fullname }}
                <!-- /ko -->
            <!-- ko if: ($index()+1) < ($parent.contributors.length) -->&nbsp;- <!-- /ko -->
            </span>
        </p>
        <!-- /ko -->
        <!-- ko if: tags.length > 0 -->
        <div data-bind="template: 'tag-cloud'"></div>
        <p><strong>Jump to:</strong>
            <a data-bind="attr.href: wikiUrl">Wiki</a> -
            <a data-bind="attr.href: filesUrl">Files</a>
        </p>
        <!-- /ko -->
    </script>
    <script type="text/html" id="project">
      <div data-bind="template: {name: 'node', data: $data}"></div>
    </script>
    <script type="text/html" id="component">
      <div data-bind="template: {name: 'node', data: $data}"></div>
    </script>
    <script type="text/html" id="registration">
        <h4><a data-bind="attr.href: url">{{ title }}</a>  (<!-- ko if: is_retracted --><span class="text-danger">Retracted</span> <!-- /ko -->Registration)</h4>
        <p data-bind="visible: description"><strong>Description:</strong> {{ description | fit:500 }}</p>

        <!-- ko if: contributors.length > 0 -->
        <p>
            <strong>Contributors:</strong> <span data-bind="foreach: contributors">
                <!-- ko if: url -->
                    <a data-bind="attr.href: url">{{ fullname }}</a>
                <!-- /ko-->
                <!-- ko ifnot: url -->
                    {{ fullname }}
                <!-- /ko -->


            <!-- ko if: ($index()+1) < ($parent.contributors.length) -->&nbsp;- <!-- /ko -->
            </span>
        </p>
        <!-- /ko -->
        <!-- ko if: tags.length > 0 -->
        <div data-bind="template: 'tag-cloud'"></div>
        <p><strong>Jump to:</strong>
            <a data-bind="attr.href: wikiUrl">Wiki</a> -
            <a data-bind="attr.href: filesUrl">Files</a>
        </p>
        <!-- /ko -->
    </script>
    <script id="tag-cloud" type="text/html">
        <p data-bind="visible: tags.length"><strong>Tags:</strong>
            <span class="tag-cloud" data-bind="foreach: tags">
                <span class="cloud-tag tag-sm pointer tag-container"
                      data-bind="click: $root.clickTag.bind($parentContext, $data, 'add')">
                    <span class="cloud-text" data-bind="text: $data"></span>
                    <i class="fa fa-times-circle remove-tag"
                       data-bind="click: $root.clickTag.bind($parentContext, $data, 'remove')"></i>
                </span>
            </span>
        </p>
    </script>
</%def>

<%def name="javascript_bottom()">
    <script type="text/javascript">
        window.contextVars = $.extend(true, {}, window.contextVars, {
            search:true
        });
    </script>

    <script src=${"/static/public/js/search-page.js" | webpack_asset}></script>


</%def>
