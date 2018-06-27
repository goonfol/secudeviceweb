$(document).ready(function () {
    // Use a "/test" namespace.
    // An application can open a connection on multiple namespaces, and
    // Socket.IO will multiplex all those connections on a single
    // physical channel. If you don't care about multiple channels, you
    // can set the namespace to an empty string.
    namespace = '/test';

    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": true,
        // "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": true,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        // "timeOut": "5000",
        // "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    }
    

    // Connect to the Socket.IO server.
    // The connection URL has the following format:
    //     http[s]://<domain>:<port>[/<namespace>]
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    // Event handler for new connections.
    // The callback function is invoked when a connection with the
    // server is established.
    socket.on('connect', function () {

        socket.emit('my_event', {
            data: 'I\'m connected!'
        });
        toastr.success("Welcome to Secuvallence, All Modules Functioning");
    });

    // flame response 
    socket.on('flame_response', function (msg) {
        // console.log(msg);
        
        $('#smoke_fire_id').html(msg.flame);
        if (msg.flame){
            $('#log').append('<br>' + $('<div/>').text('Received #' + msg.time + ': ' + msg.flame).html());
            toastr.error("Fire/Gas/Smoke Detected!", 'Alarm!!!', {
                timeOut: 10000,
                "tapToDismiss": false,
                "timeOut": 0,
                "extendedTimeOut": 0,
                "progressBar": false,
            });
        }
    });

    // temp_hum response 
    socket.on('temp_hum_response', function (msg) {
        // console.log(msg);
        $('#temp_id').html(msg.temp);
        $('#hum_id').html(msg.hum);

        $('#log').append('<br>' + $('<div/>').text('Received Temp+Hum: ' + msg.temp + ', ' + msg.hum + ' @ ' + msg.time).html());
    });

    // motion response 
    socket.on('motion_response', function (msg) {
        // console.log(msg);
        $('#motion_id').html(msg.detected);
        if (msg.detected) {
            $('#log').append('<br>' + $('<div/>').text('Received Motion #' + msg.time + ': ' + msg.detected).html());
            toastr.warning('Unusual Motion Detected!', {
                "tapToDismiss": false,
                "timeOut": 10000,
                "extendedTimeOut": 0,
                "progressBar": false,
            });
        }
    });
    // vibration response 
    socket.on('vibration_response', function (msg) {
        // console.log(msg);
        $('#vibration_id').html(msg.detected);
        if (msg.detected) {
            $('#log').append('<br>' + $('<div/>').text('Received Vibration #' + msg.time + ': ' + msg.detected).html());
            toastr.warning('Unusual Vibration Detected!', {
                "tapToDismiss": false,
                "timeOut": 10000,
                "extendedTimeOut": 0,
                "progressBar": false,
            });
        }
    });
    // magnetic response 
    socket.on('magnetic_response', function (msg) {
        // console.log(msg);
        if (msg.state) {
            $('#magnetic_id').html("Open");
            $('#log').append('<br>' + $('<div/>').text('Door Open #' + msg.time + ': ' + msg.state).html());
        }
        else {
            $('#magnetic_id').html("Closed");
            $('#log').append('<br>' + $('<div/>').text('Door Close #' + msg.time + ': ' + msg.state).html());
        }
        
        if (msg.state) {
            toastr.warning('Door Opened', {
                timeOut: 10000,
                "tapToDismiss": false,
                "timeOut": 0,
                "extendedTimeOut": 0,
                "progressBar": false,
            });
        }
    });
    // siren response 
    socket.on('siren_response', function (msg) {
        // console.log(msg);
        
        if (!msg.state) {
            $('#log').append('<br>' + $('<div/>').text('Received Panic Call #' + msg.time + ': ' + msg.state).html());
            $('#siren_id').html(msg.state);
            toastr.error('Got a Panic Call!!!', {
                "tapToDismiss": false,
                "timeOut": 10000,
                "extendedTimeOut": 0,
                "progressBar": false,
            });
        } else {
            $('#siren_id').html('Safe');
        }
    });

    // Interval function that tests message latency by sending a "ping"
    // message. The server then responds with a "pong" message and the
    // round trip time is measured.
    var ping_pong_times = [];
    var start_time;
    window.setInterval(function () {
        start_time = (new Date).getTime();
        socket.emit('my_ping');
    }, 1000);

    // Handler for the "pong" message. When the pong is received, the
    // time from the ping is stored, and the average of the last 30
    // samples is average and displayed.
    socket.on('my_pong', function () {
        var latency = (new Date).getTime() - start_time;
        ping_pong_times.push(latency);
        ping_pong_times = ping_pong_times.slice(-30); // keep last 30 samples
        var sum = 0;
        for (var i = 0; i < ping_pong_times.length; i++)
            sum += ping_pong_times[i];
        $('#ping-pong').text(Math.round(10 * sum / ping_pong_times.length) / 10);
    });
});