# Certificates

It is necessary to generate self-signed certificates for development.
If that didn't make sense, read on!

## What are certificates and certificate authorities?

[Public key certificates][certificate] are used in cryptography to prove the authenticity of a public key.
More specifically,
they are used in TLS/HTTPS communication to prevent [man in the middle attacks][mitm].
When the browser wants to send an encrypted request to `blind-guild.org`,
it receives the server's public key as part of the opening handshake.
Here, certificates come into play!

The certificate is basically a file that says
"the public key of `blind-guild.org` is BLAHBLAHBLAH."
It is signed by a certificate authority.
That authority is in turn certified by another certificate authority,
which is *also* certified by another CA...
all the way up the CA chain!
At the end of the chain, there are a few "root certificate authorities".
They are managed usually managed by a component of the operating system.

[certificate]: https://en.wikipedia.org/wiki/Public_key_certificate
[ca]: https://en.wikipedia.org/wiki/Certificate_authority
[mitm]: https://en.wikipedia.org/wiki/Man-in-the-middle_attack

## Why do we care about HTTPS

Normally, we only care about HTTPS for production builds
– we let the reverse proxy handle yucky stuff like that!
We can do that because we don't care about (our own) security when developing
and because `localhost` is considered a [secure context][sec-ctx],
meaning we still have access to all the sweet features
that are normally limited to pages served over HTTPS.

Unfortunately for us,
battle.net's API requires a HTTPS callback URI  and does *not* make any exceptions for `localhost`.
See [the documentation][ssl-req] for more details.
**So we must generate SSL certificates anyways.**

[sec-ctx]: https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts
[ssl-req]: https://develop.battle.net/documentation/guides/using-oauth#:~:text=to%20begin%20working.-,Redirect%20URL,-Developers%20registering%20an

## Creating self-signed certificates

For development can get by with self-signed certificates.
Normally,
you have to pay a certificate authority for the privilege of
them signing your certificate signing request.
For development (and a school project),
this is a bit too much work.
Instead,
we'll set up our own local certificate authority and use *that* to sign our development server's certificate.

To generate the stuff in `pki/`,
I largely followed the procedure layed out in [this SO answer][self-pki].
I did, however,  change days of validity from 365 to 328500 (900 years).
That way,
I can just check this stuff in to version control,
and hopefully no-one else will have to bother with generating them.
For reference,
here is a transcript of my terminal session:

```sh
$ openssl req -x509 -nodes \
  -newkey RSA:2048       \
  -keyout root-ca.key    \
  -days 328500           \
  -out root-ca.crt       \
  -subj '/CN=root_CA_for_firefox'
Generating a 2048 bit RSA private key
.....................................+++++
....................................................................................................................................................................+++++
writing new private key to 'root-ca.key'
-----
$ ls
root-ca.crt  root-ca.key
$ cat root-ca.*
-----BEGIN CERTIFICATE-----
MIICujCCAaICCQCgquJyWnHovTANBgkqhkiG9w0BAQsFADAeMRwwGgYDVQQDDBNy
b290X0NBX2Zvcl9maXJlZm94MCAXDTI0MDQyNDE4MTEyNVoYDzI5MjMwOTE5MTgx
MTI1WjAeMRwwGgYDVQQDDBNyb290X0NBX2Zvcl9maXJlZm94MIIBIjANBgkqhkiG
9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0VJEJ+DTEUe85ulf92HjDT6Xr4cDyS+uMJq3
fNJkLOaMhptVtwGxtL4lh1vO8j9IZVLJ611VjXjAF06cjHgDsCMJ5Rf+05tUtxLW
Z+QWFwNOS1VCDPpqEq0J+KrD9cuxLKK7nD5bPLxoXXmL3GN4v5kWqkMYDn0R66Nd
IWCF8Wkgw2MLASIiB5tbYb7xJkpfioTfH3xQBlNtAaU1mtWAHZ2W+oyawcylSKFQ
IymkjJvCjqRubLf+6q4MXpQC57wS7T+qxW1GRwpF6c5Vkx3bF9d9kXpaWDims6rs
eevsA2mLhtfJ0RN5AU7spyaIGlHvK2NhSXVnBU8nLedX2qHgCQIDAQABMA0GCSqG
SIb3DQEBCwUAA4IBAQAZzYQ9B9Lj2oxFMPQ3Eb1fI7zfFxUH1+YCX3J3oAGFd3em
LTrIZG0IjSdqvSLrkp3/IxVKCx5uEc40UjLSsN9HNqDmF0vVNNfKS4UiuFVEY7wE
22y9LkCNxYvdKz7iA1Q3m9dyWUUTSrve7zmnnDdnNBXY1lvjBr6EAgDbY8/xVyIE
4f5+3icYTjFLsdjlkjc7F3RJAKDfeO4CHl6I82QD21UO/hv4b1t7r7ZUfr1RYWb/
Tv75ISwfBfuge33H0rOIpORY5g7yZSDE58YiRFGgG8kPsOdY3N9y2T5wVDXRHs01
eJlWXed7w4P7O9NGpwuwrZmrz3RptyqAIlrAaK0u
-----END CERTIFICATE-----
-----BEGIN PRIVATE KEY-----
MIIEwAIBADANBgkqhkiG9w0BAQEFAASCBKowggSmAgEAAoIBAQDRUkQn4NMRR7zm
6V/3YeMNPpevhwPJL64wmrd80mQs5oyGm1W3AbG0viWHW87yP0hlUsnrXVWNeMAX
TpyMeAOwIwnlF/7Tm1S3EtZn5BYXA05LVUIM+moSrQn4qsP1y7EsorucPls8vGhd
eYvcY3i/mRaqQxgOfRHro10hYIXxaSDDYwsBIiIHm1thvvEmSl+KhN8ffFAGU20B
pTWa1YAdnZb6jJrBzKVIoVAjKaSMm8KOpG5st/7qrgxelALnvBLtP6rFbUZHCkXp
zlWTHdsX132RelpYOKazqux56+wDaYuG18nRE3kBTuynJogaUe8rY2FJdWcFTyct
51faoeAJAgMBAAECggEBAKSyEthBqDDHfhU9eHmftlNcdWLxW4Q3lNm/UjHPJGzD
tbvPiqCkn5rzpXmcPfcS3baDbkZXOJJIePOdscVARL6YwxdTSvhaFky5cKNrrgnL
WxYg7ghiG4W4SskyK19BNpVFMVJdKdJe98rccLQmPAKcxF2QzuPPeoMqFYPGe30W
aw4i8ZunXxriQ6kdXHG+QhP0JZVIpHwBlxwJ0R3jM2kZgcJk888HGt2AQZ6fHfoC
HM0cE6fCKebR+NbujNOFc7UXSMUyEXkkvOlk+r/kxGeE4INP1o27utItYNuNpFqD
iB+uupH/Q2xxSJ4Cke43sMzlrImjFibMvp/WcfBoxdECgYEA6+7RQCC4CQXg9tYY
N6lkU5qjKfxiXlCj1ZCpX5lW34MbWgDTc2OpCkE5dbc1wSzwblpBdUe3NHVVMTu7
7yVvvytfH8dEasb5BWgkFdqNyPzoaP9wN6TC1cyuKsbYmbq7NTM9D1Q5dTtsjGfO
3PBVUlj3RxHTKj6roAO+D2P3J20CgYEA4yAC/eUZ5ANk9YZrIGsoFjPqYMlKXDUO
uQnnaSnKcL5E68ehvVvKj5epY/EicsGEKgEeIphJgley9x9AsU40UnlI3/bzqIhV
GRjHPxiV7W9pB+PR4JWhppgohkIz3/QD4RONQNYYot7Jx+/QP9IAO1Br8kP80BEE
4HrlNuT/LY0CgYEAz/Qm4hQ0wlc5K7gXjnAy6vHhIS/A8Iq5bZNdhtLcXJPt9s3F
ku5j35MP927t5YAbx9ir25jDpWxKE+QnySlBLsomxRbZehg5BAf/zndeA6rPm0SS
/6isxs/rL+8mmZGaUtD/39QH9QnUqokRL3JycevSwQS4EIM+uQKzclNVVJ0CgYEA
zSSKzzxxCCuwsrs4Y02mJXe6yLTG/0XFCIjThX8DpJWWtsfXZKtV6CB6FRUlojT7
5NyhlWmra5k+wkpuKjeStrNpiTEKnzyUcFibDnhsYsrwOPojBRDhsxFX+Pwu0qca
Id+BBADcu68y3e3TUPGi1/Apr+aMoHnex8r44X4wpbkCgYEA33ozRucqlq6IaXVJ
khESj6rv0CIa0dNUYVR+IuXQTj6MuQhY31BgsQOonSS6I5UsdD2z3Bj0MFz0wN1J
V/rWseLJbFEgZiFyClhZKSe3oom7ehZvbPBYmWAg+kiUBav/823IJ3JQZQ8t1jU/
Mk0B0PEYP3KTTMwiO7uEnC73l7c=
-----END PRIVATE KEY-----
$ openssl req -nodes \
  -newkey rsa:2048   \
  -keyout server.key \
  -out server.csr    \
  -subj '/CN=localhost'
Generating a 2048 bit RSA private key
...............+++++
...........................................+++++
writing new private key to 'server.key'
-----
$ openssl x509 -req
  -CA root-ca.crt    \
  -CAkey root-ca.key \
  -in server.csr     \
  -out server.crt    \
  -days 328500       \
  -CAcreateserial    \
  -extfile <(printf "subjectAltName = DNS:localhost\nauthorityKeyIdentifier = keyid,issuer\nbasicConstraints = CA:FALSE\nkeyUsage = digitalSignature, keyEncipherment\nextendedKeyUsage=serverAuth")
Signature ok
subject=/CN=localhost
Getting CA Private Key
$ ls
root-ca.crt  root-ca.key  root-ca.srl  server.crt   server.csr   server.key
```

[self-pki]: https://stackoverflow.com/a/77009337

## Trusting self-signed certificates

Now, the browser obviously doesn't trust this certificate
– nor should it!
It doesn't know anything about our local CA,
so this certificate may as come from a malicious actor.
If you attempt to load https://localhost:8080
without performing the steps in this section,
the browser will give you an error like `NET::ERR_CERT_AUTHORITY_INVALID`.

For development purposes
we would like to inform the browser
that this CA is indeed to be trusted.
The process varies a bit between different combinations of browsers and operating systems.
Firefox, for example, maintains its own list of CAs.
[Here][ff-trust] is a guide on how to install our custom CA into Firefox's trust store.
Chrome, on the other hand, seems to be using the operating system's certificate store,
so you'll need to modify this instead.
[Here][guide-win] is a guide on how to do it on Windows
and [here][guide-osx] is a guide for MacOS.

N.B. Always keep in mind that we are looking to install our CA, that is the file `pki/root-ca.crt`, NOT the servers certificate, found in `pki/server.crt`.

[ff-trust]: https://javorszky.co.uk/2019/11/06/get-firefox-to-trust-your-self-signed-certificates/
[guide-win]: https://techcommunity.microsoft.com/t5/windows-server-essentials-and/installing-a-self-signed-certificate-as-a-trusted-root-ca-in/ba-p/396105
[guide-osx]: https://tosbourn.com/getting-os-x-to-trust-self-signed-ssl-certificates/

## Chrome is annoying

For Firefox, the above is enough.
It nags you a bit but you can force it to pipe down.
When presented with the warning,
just click "Advanced" and then "continue".

Not so much for Chrome.
It still complains about an invalid CN (common name).
Luckily, there's one final escape hatch:
type "[thisisunsafe]" anywhere on the error page.

[thisisunsafe]: https://cybercafe.dev/thisisunsafe-bypassing-chrome-security-warnings/
