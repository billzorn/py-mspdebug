#lang racket

(provide
 ; creation and destruction
 mspdebug-init mspdebug-close
 ; status info
 mspdebug-tty mspdebug-status
 ; interface
 msp-reset
 msp-prog
 msp-mw
 msp-fill
 msp-setreg
 msp-md
 msp-regs
 msp-step
 msp-run
 ; bonus
 msp-read-word
 msp-read-dword)

; For simplicity, we'll keep this simple and provide a struct type
; and a bunch of methods that act on it; a better programming paradigm
; might use something like objects.

(struct mspdebug (sp sp-stdout sp-stdin sp-stderr tty))

(define (mspdebug-close mspd)
  (close-output-port (mspdebug-sp-stdin mspd))
  (subprocess-wait (mspdebug-sp mspd))
  (let ([stdout-data (port->string (mspdebug-sp-stdout mspd))]
        [stderr-data (port->string (mspdebug-sp-stderr mspd))])
    (close-input-port (mspdebug-sp-stdout mspd))
    (close-input-port (mspdebug-sp-stderr mspd))
    (values
     (subprocess-status (mspdebug-sp mspd))
     stdout-data
     stderr-data)))

(define (mspdebug-init)
  (let*-values
      ([(sp sp-stdout sp-stdin sp-stderr) (subprocess #f #f #f (find-executable-path "pymspdebug"))]
       [(ack) (read-line sp-stdout)]
       [(tty) (regexp-match #px"(?i:tty\\S*\\d+)" (string-trim ack))]
       [(mspd) (mspdebug sp sp-stdout sp-stdin sp-stderr
                         (if tty (string->symbol (first tty)) #f))])
    (if tty
        mspd
        (let-values ([(status stdout-data stderr-data) (mspdebug-close mspd)])
          (raise-user-error 'mspdebug-init "~a\n(driver returned ~a)\nstdout: ~a\nstderr: ~a"
                            ack status stdout-data stderr-data)))))

(define (mspdebug-status mspd)
  (subprocess-status (mspdebug-sp mspd)))

; internal
(define (mspdebug-cmd mspd cmd)
  (displayln cmd (mspdebug-sp-stdin mspd))
  (flush-output (mspdebug-sp-stdin mspd))
  (read-line (mspdebug-sp-stdout mspd)))

; string helpers
(define (hex->number s)
  (string->number (string-replace (string-replace s "0x" "") "0X" "") 16))
(define (number->hex x)
  (format "0x~x" x))
(define (msp-ok? s)
  (false? (regexp-match #rx"(?i:^err)" s)))

; Standard interface, with string/integer conversion

(define (msp-reset mspd)
  (hex->number (mspdebug-cmd mspd "reset")))

(define (msp-prog mspd fname)
  (let ([abspath (path->complete-path fname)])
    (if (file-exists? abspath)
        (let ([data (mspdebug-cmd mspd (format "prog ~a" abspath))])
          (if (msp-ok? data)
              (hex->number data)
              (raise-argument-error 'msp-prog "path to executable file" data)))
        (raise-argument-error 'msp-prog "path to executable file" abspath))))

(define (msp-mw mspd addr pattern)
  (mspdebug-cmd mspd (format "mw 0x~x ~a" addr (string-join (map number->hex pattern))))
  (void))

(define (msp-fill mspd addr size pattern)
  (mspdebug-cmd mspd (format "fill 0x~x ~a ~a" addr size (string-join (map number->hex pattern))))
  (void))

(define (msp-setreg mspd rn x)
  (mspdebug-cmd mspd (format "setreg ~a 0x~x" rn x))
  (void))

(define (msp-md mspd addr size)
  (map hex->number (string-split (mspdebug-cmd mspd (format "md 0x~x ~a" addr size)))))

(define (msp-regs mspd)
  (map hex->number (string-split (mspdebug-cmd mspd "regs"))))

(define (msp-step mspd)
  (hex->number (mspdebug-cmd mspd "step")))

(define (msp-run mspd seconds)
  (hex->number (mspdebug-cmd mspd (format "run ~a" seconds))))

; Bonus interface

; endianness
(define (le-word bytepair)
  (bitwise-ior (first bytepair) (arithmetic-shift (second bytepair) 8)))
(define (le-dword bytequartet)
  (bitwise-ior
   (first bytequartet)
   (arithmetic-shift (second bytequartet) 8)
   (arithmetic-shift (third bytequartet) 16)
   (arithmetic-shift (fourth bytequartet) 24)))

(define (msp-read-word mspd addr)
  (le-word (msp-md mspd addr 2)))

(define (msp-read-dword mspd addr)
  (le-dword (msp-md mspd addr 4)))

