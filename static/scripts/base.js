;
"use strict";

var Nemesis = Nemesis || {
        State: {
            current_task: null,
            selected_terms: []
        },
        event_handlers: function () {
            var context = Nemesis,
                //replace to working area only if possible
                workplace = $(document.body);

            workplace.on("click", "a#save-button", function (e) {
                e.preventDefault();
            });

            // be able to call methods fluently
            return context;
        },
        load_next: function (data) {
            Nemesis.State.current_task.css("visibility", "visible").html(data);
            Nemesis.State.init_task_stuff(Nemesis.State.current_task);
        },
        /* http://xkcd.com/292/ */
        init_task_stuff: function (task) {
        },
        init: function () {
            var ne = this;

            $.ajaxSetup({traditional: true});

            $(function () {
                ne.State.current_task = $("#current_shred");
                ne.event_handlers();
            });
        }
    };

Nemesis.init();