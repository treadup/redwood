# GPG
This page contains instructions for creating, exporting and importing GPG keys.

## Creating Keys
To create a new GPG key use the following command.

    gpg --full-generate-key

## Exporting Keys
To export your public and private GPG keys use the following commands.

```
gpg -a --export henrik.treadup@gmail.com > henrik-public-gpg.key
gpg -a --export-secret-keys henrik.treadup@gmail.com > henrik-secret-gpg.key
gpg --export-ownertrust > henrik-ownertrust-gpg.txt
```

## Importing Keys
To import your public and private GPG keys use the following commands.

```
gpg --import henrik-secret-gpg.key
gpg --import-ownertrust henrik-ownertrust-gpg.txt
```

## Trusting Keys
If you forget to import the owner trust you must manually tell GPG that
you trust a key.

    gpg --edit-key henrik.treadup@gmail.com

Then at the GPG prompt you issue the trust command.

    > trust

The trust level for the key should be ultimate trust.

## Public GPG key
This is my public GPG key.

    -----BEGIN PGP PUBLIC KEY BLOCK-----

    mQENBFYry+QBCAC3qESZEIxJFDON4ISskeX99QzAtps0CuBlGtD+8U2PZPYdMvTX
    nGViJuSdN8RbfncUUU9YKumGfWH62eAxWKS9+WnBP3rSMTx20l+IrqvNofbU9wDh
    gxdVateKkGHe+lgTNQoW7tF0mR+JcEcYxYONJCix51ICkCvAGW0i9ZWW4sxqImsN
    nrhNSO2J/pQ6/BEylh+HbCRNj6FMwi3IuDllMbw7bimusytQM/qu6KrVKGoq4zjC
    VPY+4RgsgrXsRojFVtizGUHSvKj+y8/JuA/boL2DwTwC1U4k0aqrgEA0BdI3TX9f
    olYnAeSAXozY40He3lxqqWnomQAwPCXDuN07ABEBAAG0KUhlbnJpayBUcmVhZHVw
    IDxoZW5yaWsudHJlYWR1cEBnbWFpbC5jb20+iQE4BBMBAgAiBQJWK8vkAhsDBgsJ
    CAcDAgYVCAIJCgsEFgIDAQIeAQIXgAAKCRD1uOmtvz85y3erCAC1xJUPuzNAm8zH
    Lnlc98kXse374FcDDtaqEvs4qeIu2T3bsTwg4/V5sEVZod6yx9GZZQ1/OwiY8E2d
    geWQU3YkOq1vbXq6E4URGCBp0sDzx/6J2Wj3WkLN8Yk4IK8G8AFRWB+84KEierE8
    FhTfPECeZgxA2mDA8eBnMXEltJoK+qIGL1jSv4vJKK0uSJZaZMH5Y8oUidzozJ3/
    afxXa9ew9sbaVv9YcxbB0wQ+9aQXv/RIezwLgndFM05KWu2uW8Rq4zzG4B+0jTfL
    DktpwiV2LBtUOmOuC8h/+Wh6pvnQlMzUm5xaxzFQZk/mrnP/OUYbq89Dz2S5Hvfj
    QYmlJAXIuQENBFYry+QBCAC97ZpmmyeSQAP2Os2Lf+3+4zuysEzpXokPyhSTs95V
    Sv0Hh3V+Lbtn9qjWANLjC3gHKhR9Jz8lNdS7hUgihDlunB/hjtSPWrTbQ/no/DZd
    Br7pRHwQx2xsm9BcR+7eX5VXwI4/jklXMNiOm/fROUG6UIT+xQcPXwdnZnvp+fFN
    Tk8vbZNlSRuWHpjkZAwzMCzPFQiBo7+tt0YEt6p69qOJ8Du5VS5m4YrDU0nDc2MP
    TvEPA7NFUADDCHJ0GceZ3W8rPoCiS21SPt7WfQ0suzqk02UCFf+E/uYkdh0zzeUl
    Jv2eCuA6BcsbAggVcd2V1eSeAkFszgRvnDk0hwtrRZkpABEBAAGJAR8EGAECAAkF
    AlYry+QCGwwACgkQ9bjprb8/OctNTQf/UQi31zZfYbO4mUSBa8qlXhao0pYvbEw5
    Q5GS0e5O4YbtOaMmWtdQ3eyo+KguCS7UYdzOmtQq00JJMPz/EIYWuRGHqW8suoKB
    wNY6b7xsXR55QX3W4fEeY/L38IJRYBbjW6qWMP0RVw8oNvc7BSlor320/I7TDql9
    5HC0MThUK82Kl4pgrP5pejSgcXq58WLwbU4D5pQ9g/wHytvTZZi8y9z9dydwCW6x
    jXjB9/vUyrS1nHSZ8OO5CObjevedNxymia+6u3VwN0RX0GZqDiz1yqfRt3t5g0mA
    PYIqgUgsSg5XqG+Eyx2zfU09YIulJ48ugDiO9sInGRrEjXKeb0+GPQ==
    =uDOQ
    -----END PGP PUBLIC KEY BLOCK-----
