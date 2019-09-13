# Game Development Programming Languages
The following document will go over game development in different
programming languages.

One of the first questions you have to answer is do you want to write
a game engine or game library or do you want to write a game?

## Desktop and Mobile Games
When it comes to desktop and mobile games there are a couple of things
that you have to consider.

1. Using the language which platforms can you create executables for?
2. How easy is it to create the executable?
3. Does the language have a well supported game library that works on
   all platforms you want to support?
4. Can the language/game library be used to create mobile games?
5. Can the game library be used to create fullscreen games on all
   platforms that you want to support?

Do not underestimate the effort it takes to write a cross platform
game library for a given language.

### 3D games
Since OpenGL was deprecated on macOS there is currently no cross
platform hardware accelerated library for creating 3D graphics
applications. This is kind of irritating.

I guess one could always write a software rasterizer and just ignore
OpenGL, Vulkan, Metal and Direct3D. On Linux one could even use the
framebuffer directly.

At some point in the future there might be a new cross compatible
hardware accelerated 3D API. Or someone could perhaps a translation
layer from a 3D API like OpenGL to a 3D API supported natively by the
underlying platform.

### Cross platform games
Writing a game that works on a single platform is relatively simple.
When it comes to multiplatform games the important thing is the choice
of programming language and game library. These choices are made up
front when you start coding the game. The level of complexity you
encounter when changing language or game library is about the same as
writing a completely new game from scratch. Therefore it is important
to make sure beforehand that the language and game library that you
choose will run on all the platforms you want to support.

1. Is the language supported on all platforms that I want to use?
2. Can the language be used to create native executables for all the
   platforms that I want to use?
3. Is the game library supported on all platforms that I want to use?
4. Can I write mobile games using this language and game library
   combination?

### C
For C there are a couple of different libraries for making games. For
making cross platform 2D games the main libraries are SDL and SDL2.

C is also interesting since lots of other languages have the ability
to call C code using some kind of foreign function interface. So
anything that you learn for C can be used in another language by
embedding it.

One problem with writing pure C games is that it can take a very long
time to actually develop the game. Also it can be tough to debug a
segfault in a C program.

When it comes to C there are a couple of different game libraries that
can be used.

### C++
I'm not interested in working with C++. Otherwise this is similar to
using C.

### Rust
Rust seems a bit too complex for me. It looks interesting but I do not
feel productive at all in it.

### Golang
Golang is interesting when it comes to game development. It can be
used to write both game clients and servers. I have seen examples of
people write mobile games that run on both Android and iOS using
Golang.

### Lua
Lua is a language that is easy to embed in larger programs. It is
therefore often used as a scripting language in games.

Also the Löve2D game engine is written using Lua.

### Java
Minecraft is written in Java and it is one of the most successful
games in the world. Java can be used to write Android and desktop
games. Using a packager like packr you can even create an executable
that will run on the desktop.

One popular game library for Java is libGDX.

It might be possible to run a Java game on iOS using RoboVM.

### Kotlin
Kotlin can be used to write Android and desktop games. However getting
games written in Kotlin running on iOS will probably be problematic.
This can perhaps be done with RoboVM.

### Swift
Swift can be used to write iOS mobile games and macOS desktop games.

I'm unsure if you can use swift to write games that will run on
Windows and Linux. I'm also unsure if you can use swift to make games
that will run on Android.

### Python
Python can be used to write games that run on the desktop. However I
have never tried to package a python program as a native executable.

I should probably explore this further since Python is a very simple
programming language.

### Game Engine
You can also use a game engine like Unreal Engine, Unity or Godot to
write your games. However I have never liked working with these.
Usually it is hard to get the project into source control. Also
updates to the engine can break your game since the format of the
project file can change and

With both Unity and Unreal Engine it can be problematic if you have
several developers working on the same code. It is difficult to merge
together two versions of the same scene that two different developers
have modified.

### Fennel
Fennel is a lisp that compiles to Lua. It can therefore be used with
the Löve2D game engine. Since you are using Lua under the hood you
have to have some knowledge of Lua and the Lua ecosystem.

### Urn
Urn is a lisp that compiles to Lua. It can therefore also be used
together with the Löve2D game engine. Since you are using Lua under
the hood you have to have some knowledge of Lua and the Lua ecosystem.

### Common Lisp
Common lisp can be used for game development. It is possible to call C
code from common lisp. The cl-sdl2 package provides bindings for SDL2.

One nice thing about common lisp is that it can create native
executables for the desktop. I am unsure if you can use common lisp
for mobile development.

### Scheme
Scheme is a small language. You can write programs in scheme or embed
a scheme interpreter in another program. The underlying platform could
be C, Java, Golang, etc.

It should be fairly simple to have a Scheme written in C make calls to
C functions. Such a scheme could be used with SDL or SDL2.

### Clojure
Clojure can be used to create native executables in the same way as
for Java programs. You can also use libGDX from Clojure.

There is the play-clj library which is a Clojure wrapper for libGDX.

### JVM languages
It should be possible to use any programming language that runs on the
JVM to create a game that you can distribute natively. In all of these
languages it should be possible to have bindings to libGDX.

In other words you should be able to create games using any of the
following languages.

* Armed Bear Common Lisp
* Kawa Scheme
* SISC Scheme
* Bigloo Scheme

### Forth
Forth is interesting since it is a simple language to implement.
Together with a C game library this could produce interesting results.

Forth can be used to create native applications.

### JavaScript
JavaScript can be used to create desktop and mobile applications.
However for desktop applications the RAM and hard drive resource
requirements for an Electron game are very high.

For mobile games you can use something like React Native to create a
canvas that you then use to interact with using normal JavaScript or
ClojureScript. This is probably not a bad approach but it still feels
a bit like a Rube Goldberg machine.

## Game Servers
When it comes to writing a game server you want to use a language that
has good networking support and good support for concurrent
programming.

Here are some things you have to consider when choosing programming
language for a game server.

1. Is there language level support for concurrent programming?
2. Does the language have good support for concurrent programming?
3. Do you like working with the concurrency model that the language provides?
4. Does the language have support for network programming?
5. Can you create TCP servers?
6. Can you create UDP servers?
7. Does the language support writing web applications?
8. Can the language be used to write a WebSocket server?
9. Is it easy to deploy the server once it is written?

### Golang
Golang is a very interesting language for network servers. It has
built in concurrency support with channels and goroutines. For golang
the answer is yes to all of the above questions.

One nice thing about Golang is that it can also be used to write
mobile and destop game clients.

Golang has good support for web applications and you can write
websocket servers using Golang.

### Erlang
Erlang also has excellent support for concurrent programming. It is
fairly easy to write a TCP or UDP network server using Erlang.

It is also possible to write web applications and websocket servers
using Erlang.

### Common Lisp
Common Lisp can be used to write web applications. There might be
support for WebSockets.

I'm not familiar with concurrent programming in Common Lisp.

I have never done network programming in Common Lisp.

My feeling is that it would be worth the effort to try to look more
into common lisp and see what can be done with it.

### Clojure
It is possible to write network servers in Clojure. See the Clojure
cookbook for more information on this.

Clojure does have support for concurrent programming.

Clojure is an excellent choice for writing web applications. Clojure
can be used for writing websocket servers. However this might involve
picking a specific clojure HTTP server or a specific clojure WebSocket
library.

### Python, Node, Ruby, etc
These languages do not have a good concurrency support and I do not
feel that they are the right choice when it comes to writing a network
servers.

## Browser games
Browser games are games that run inside the web browser. Using
WebSockets it is possible to create networked games.

### WebSockets
When it comes to browsers you can use WebSockets or WebRTC for
network communication. WebRTC seems way too complex so that leaves us
with WebSockets.

WebSockets can be used for bidirectional communication between client
and server over a TCP socket. First person shooters and other games
where state can change quickly usually use UDP for communication
between client and server. This is not currently possible for browser
based games.

### 3D games
For the web the situation with for 3D application development is a bit
better. WebGL and WebGL 2.0 are standardized and should therefore
hopefully be supported for quite some time. This in turn means that it
should be possible to use 3D engines that are built on WebGL or WebGL
directly to make 3D games and applications.

### Canvas vs SVG
You can create a game using the Canvas or using SVG and the DOM. From
the little reading I have done on the subject using the canvas is much
faster than using SVG and the DOM. With SVG you also have the issue
of updating the DOM just like you would with a normal HTML
application. There are solutions to this like a virtual DOM but I do
not think this would be a good idea when writing a game.

However you can use SVG images for graphics resources for your game.
On the client you can convert a SVG to an image.

### JavaScript
When writing a game you usually use the canvas and some kind of audio
library like howler.js or a JavaScript game library. It is also
possible to use the DOM and SVG to create a game.

Using JavaScript you can make a cross platform game that runs in the
browser, on the desktop and on mobile phones. You might have to use
different frameworks on each of the platforms but the core language
can stay the same.

### Compile to JavaScript languages
There are a bunch of other compile to JavaScript languages that might
be interesting to look at.

1. TypeScript
2. ClojureScript

### Game Engines
There are a bunch of different JavaScript 2D and 3D game engines. I'm
not familiar with any of these but they might be worth looking into.

### WebAssembly
I don't know enough about WebAssembly to say anything useful about it.
However if you do have an existing game that you want to run on the
web then WebAssembly might be worth looking into.

The following are some languages that can be compiled to WebAssembly.

1. C/C++
2. Rust
3. Golang
