

console.log("file loaded");

//phone serialNumber: "9888d936494e564f34"


let initReport = new Uint8Array(1);
initReport[0] = 42;

function handleInputReport(e) {
    console.log(e)
    // Fetch the value of the first button in the report.
    let buttonValue = e.data;
    console.log('Button value is ' + buttonValue);
}

const filters = [ // scanner
    { vendorId: 0x05fe, productId: 0x1010 }
];




let button = document.getElementById('request-device');
button.addEventListener('click', async () => {


    navigator.usb.requestDevice({ filters: filters })
        .then(selectedDevice => {
            device = selectedDevice;
            return device.open(); // Begin a session.
        })
        .then(() => device.selectConfiguration(1)) // Select configuration #1 for the device.
        .then(() => device.claimInterface(2)) // Request exclusive control over interface #2.
        .then(() => device.controlTransferOut({
            requestType: 'class',
            recipient: 'interface',
            request: 0x22,
            value: 0x01,
            index: 0x02
        })) // Ready to receive data
        .then(() => device.transferIn(5, 64)) // Waiting for 64 bytes of data from endpoint #5.
        .then(result => {
            let decoder = new TextDecoder();
            console.log('Received: ' + decoder.decode(result.data));
        })
        .catch(error => { console.log(error); });
    // console.log("trying connection");
    // let device;
    // try {
    //     device = await navigator.usb.requestDevice({ filters: filters });
    // } catch (err) {
    //     // No device was selected.
    // }
    // 
    // if (device !== undefined) {
    //     // Add |device| to the UI.
    // }
});

document.addEventListener('DOMContentLoaded', async () => {


    //    let devices = await navigator.usb.getDevices();
    //    console.log("Total devices: " + devices.length);
    //    devices.forEach(device => {
    //        device.open()
    //            //.then(() => device.selectConfiguration(1))
    //            //  .then(() => device.claimInterface(0))
    //            //    .then(() => device.transferIn(5, 64)) // Waiting for 64 bytes of data from endpoint #5.
    //            //    .then(result => {
    //            //        console.log('Received: ' + result.data);
    //            //    })
    //            .catch(error => { console.log(error); });
    //        console.log("Product name: " + device.productName + ", serial number " + device.serialNumber);
    //        console.log(device)
    //        //device.addEventListener('inputreport', handleInputReport);
    //    });
    //    //let receivedData = await data.transferIn(1, 6);// Waiting for 6 bytes of data from endpoint #1.
    //    //console.log(receivedData);

});

navigator.usb.addEventListener('connect', event => {
    console.log(event.device);
    console.log("...connected");
    event.device.addEventListener('inputreport', handleInputReport);
});

navigator.usb.addEventListener('disconnect', event => {
    console.log(event.device);
    console.log("...disconnected");
});












// navigator.usb.requestDevice({ filters: filters })
//     .then(usbDevice => {
//         usbDevice.open().then(() => {
//             console.log('Opened HID device');
//             usbDevice.addEventListener('inputreport', handleInputReport);
//             usbDevice.sendReport(0x01, initReport).then(() => {
//                 console.log('Sent initialization packet');
//             });
//         });
//         console.log("Product name: " + usbDevice.productName);
//     })
//     .catch(e => {
//         console.log("There is no device. " + e);
//     });



