;
"use strict";

var Vulyk = Vulyk || {
        State: {
            workplace: null,
            task_type: "",
            task_title: "",
            task_id: 0,
            task_init_state: null,
            task_state: null,
            task_wrapper: null,
            selected_terms: []
        },
        event_handlers: function () {
            var vu = Vulyk;

            vu.State.workplace
                .on("click", "a#save-button", function (e) {
                    e.preventDefault();
                })
                .on("click", ".mfp-close", function (e) {
                    e.preventDefault();

                    vu.show_types_selector();
                    vu.State.workplace.find(".mfp-hide").hide();
                });

            // be able to call methods fluently
            return vu;
        },
        remap_text: function () {
        },
        load_next: function () {
            var vus = Vulyk.State,
                meta = null;

            $.get(
                "/type/" + vus.task_type + "/next",
                function (data) {
                    vus.task_wrapper.html(data);

                    meta = $.parseJSON(
                        vus.task_wrapper
                            .find("#task_meta")
                            .attr('data-payload'));
                    vus.task_id = meta.id;
                    vus.task_title = meta.title;
                    vus.task_init_state = vus.task_state = meta.structure;
                },
                "html");
        },
        show_types_selector: function () {
            var vus = Vulyk.State;

            $.get(
                "/types",
                function (data) {
                    var task_list = vus.task_wrapper.empty().append(
                            $('<ul class="tasklist">')),
                        task_type;

                    for (var i=0; i < data.result.types.length; i++) {
                        task_type = data.result.types[i];
                        task_list.append(
                            $('<li><a href="/type/' + task_type + '/">' + task_type + '</a></li>'))
                    }

                }, "json");
        },
        skip_task: function () {
            var vus = Vulyk.State;

            $.post(
                "/type/" + vus.task_type + "/skip" + vus.task_id,
                {},
                function(data){},
                "json");
        },
        save_report: function () {
            var vus = Vulyk.State;
            // TODO: Breathe the life into this barren method.
            $.post(
                "/type/" + vus.task_type + "/done" + vus.task_id,
                {},
                function(data){},
                "json");
        },
        /* http://xkcd.com/292/ */
        init: function () {
            var vu = this;

            $.ajaxSetup({traditional: true});

            $(function () {
                vu.State.workplace = $(".site-wrapper");
                vu.State.task_wrapper = vu.State.workplace.find("#current_task");
                vu.event_handlers();
            });
        }
    };

Vulyk.init();
