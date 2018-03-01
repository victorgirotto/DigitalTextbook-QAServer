var CLASSIFICATION = function(){

    var steps = {
        type: "question",
        question: "Does this message reply or refer to another user's message?",
        options: [
            {
                label: "YES",
                nextStep: {
                    type: "question",
                    question: "Does this message build on another user's message(s)?",
                    options: [
                        {
                            label: "YES",
                            nextStep: {
                                type: "question",
                                question: "Choose the option that best describes how this message is building on the other one.",
                                options: [
                                    {
                                        label: "CLARIFICATION/EXTENSION",
                                        nextStep: {
                                            type: 'classification',
                                            classification: "OPER_CLARIFEXT"
                                        }
                                    },
                                    {
                                        label: "COUNTER EXAMPLE",
                                        nextStep: {
                                            type: 'classification',
                                            classification: "OPER_COUNTEREX"
                                        }
                                    },
                                    {
                                        label: "CRITIQUE/CONTRADICTION",
                                        nextStep: {
                                            type: 'classification',
                                            classification: "OPER_CRITCONTRADICT"
                                        }
                                    },
                                    {
                                        label: "COMBINING VIEWS",
                                        nextStep: {
                                            type: 'classification',
                                            classification: "OPER_COMBINATION"
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            label: "NO",
                            nextStep: {
                                type: "question",
                                question: "Does this message ask for more information or for confirmation?",
                                options: [
                                    {
                                        label: "YES",
                                        nextStep: {
                                            type: 'classification',
                                            classification: "REPR_QUERY"
                                        }
                                    },
                                    {
                                        label: "NO",
                                        nextStep: {
                                            type: 'classification',
                                            classification: "REPR_STATEMENT"
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            },
            {
                label: "NO",
                nextStep: {
                    type: 'classification',
                    classification: "NOTRANSACT"
                }
            }
        ]
    }; 

    var runNextStep = function(currentStep, button){
        // Get next step
        var nextStep = currentStep.nextStep;
        var taskArea = $(button).parents('.taskArea');
        var choicesContainer = $(button).parent();
        if(nextStep.type === 'question'){
            // Update taskArea
            taskArea.animate({width: '450px'}, 500, 'swing').width('450px');

            // Update content
            $('p', taskArea).text(nextStep.question);
            choicesContainer.empty();
            var choices = nextStep.options;
            choices.forEach(function(d,i){
                var choice = $('<a>' + d.label + '</a>');
                choice.click(function(e){ runNextStep(d, e.target); });
                choicesContainer.append(choice).attr({});
            });
        } else {
            classify(nextStep.classification, taskArea);
        }
    };

    var addTask = function(chatPanel){
        // <div>
        // 	<p>Does this message reply or refer to another user's message?</p>
        // 	<div class="choices">
        // 		<a href="#">Yes</a>
        // 		<a href="#">No</a>
        // 	</div>
        // </div>
        
        // Get current step
        var step = steps;
        // Create and append element
        var innerContainer = $('.chatMessage',chatPanel);
        var message = step.question;
        var taskArea = $('<div class="taskArea"><div><p>'+message+'</p><div class="choices"></div></div></div>')
        innerContainer.append(taskArea);
        // Set classes
        innerContainer.removeClass('notask');
        // Set options
        var optionsContainer = $('.choices', chatPanel);
        var choices = steps.options;
        choices.forEach(function(d,i){
            var option = $('<a>' + d.label + '</a>');
            option.click(function(e){ runNextStep(d, e.target); });
            optionsContainer.append(option).attr({});
        });
    };

    var classify = function(classification, taskArea){
        var chatPanel = taskArea.parents('.chatPanel');
        var id = chatPanel.data('id');
        var reply_author = chatPanel.data('user')
        $.ajax({
            method: 'POST',
            url: URL.classify,
            data: {
                classification: classification, 
                id: id,
                reply_author: reply_author
            },
            success: function(data){
                closeTask(taskArea);
                updateContributionPoints(data);
            },
            error: function(){
                alert('something went wrong');
            }
        })
    }

    var closeTask = function(taskArea){
        var chatPanel = taskArea.parents('.chatPanel');
        chatPanel.removeClass('notClassified');
        taskArea.fadeOut('slow', function(){
            taskArea.remove();
        })
    };

    return {
        addTask: addTask
    }

}();
