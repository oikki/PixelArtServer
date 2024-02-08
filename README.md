## Server for uploading images from VRChat
![Preview picture](https://github.com/oikki/PixelArtServer/blob/main/preview_images/pixel_arts.png)

This is a API server for communicating VRChat. It is used to store the pixel art's made by the users in the world. 

VRChat has several limitations when sending data that include:
- You can only use hard-coded URLs in your project. You can't create URLs at runtime without direct user input.
- Max 1 http request per 5 seconds
- Http request can only contain the url and you can't modify the headers. So basically you communicate only by using GET requests
- you can't use cookies

Because you can't send the authenticataion with the http request, we use the users IP address to indentify the user.
The usernames are converted to unicode and these characters are sent one at the time and put together in server.

As for sending the picture data, I have 16 different colors available in the game so sending 4 pixels at the time requires 2^16=65536 hard-coded urls for all possible color combinations. 
Also the urls for liking the pixel art's need to be hard-coded.


![Preview picture](https://github.com/oikki/PixelArtServer/blob/main/preview_images/uploading_picture.png)
