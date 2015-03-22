;
"use strict";

var Vulyk = Vulyk || {
        State: {
            workplace: null,
            body: null,
            task_type: "",
            task_title: "",
            task_id: 0,
            task_init_state: null,
            task_state: null,
            task_wrapper: null,
            selected_terms: []
        },
        event_handlers: function () {
            var vu = this,
                vus = vu.State;

            vu.State.workplace
                .on("click", "a#save-button", function (e) {
                    e.preventDefault();
                    vus.body.trigger("vulyk.save", vu.save_report.bind(vu));
                })
                .on("click", "a#skip-button", function (e) {
                    e.preventDefault();
                    vus.body.trigger("vulyk.skip", vu.skip_task.bind(vu));
                });

            return vu;
        },

        load_next: function () {
            var vus = Vulyk.State,
                meta = null;

            $.get(
                "/type/" + vus.task_type + "/next",
                function (data) {
                    vus.task_id = data.result.task.id;
                    vus.body.trigger("vulyk.next", data);
                }
            ).fail(function() {
                // TODO: no more tasks to do
                alert("Error occurred or no unassigned tasks left");
            });
        },
        skip_task: function () {
            var vu = this,
                vus = vu.State;

            $.post(
                "/type/" + vus.task_type + "/skip/" + vus.task_id,
                {},
                function(data){
                    vu.load_next()
                }
            );
        },
        save_report: function (result) {
            var vu = this,
                vus = vu.State;

            $.post(
                "/type/" + vus.task_type + "/done/" + vus.task_id,
                {result: JSON.stringify(result)},
                function(data) {
                    vu.load_next()
                });
        },
        /* http://xkcd.com/292/ */
        init: function () {
            var vu = this;

            $.ajaxSetup({traditional: true});

            $(function () {
                vu.State.workplace = $(".site-wrapper");
                vu.State.body = $(document.body);
                vu.State.task_wrapper = vu.State.workplace.find("#current_task");
                vu.event_handlers();

                if (vu.State.task_wrapper.length) {
                    vu.State.task_type = vu.State.task_wrapper.data("type")
                    vu.load_next();
                }

                $('.popup-with-zoom-anim').magnificPopup({
                    type: 'inline',

                    fixedContentPos: false,
                    fixedBgPos: true,
                    overflowY: 'auto',
                    closeBtnInside: true,
                    preloader: false,

                    midClick: true,
                    removalDelay: 100,
                    mainClass: 'my-mfp-zoom-in'
                });
            });
        }
    };

Vulyk.init();
