<?php
declare(strict_types=1);

/* ==========================================================================
   EMORPHOSIS — Mailer Otimizado para Caixa de Entrada Principal (Main Inbox)
   - Remetente / Reply-To oficial do projeto: emergentmetamorphosis@gmail.com
   - Formato text/plain conversacional 1-para-1 (sem caixas HTML pesadas, sem
     "noreply", sem cabeçalhos de disparo em massa e sem rodapés promocionais),
     evitando que o Gmail classifique na aba "Atualizações" ou "Promoções".
   - Suporta envio via SMTP direto do Gmail (caso haja senha de app em
     api/storage/smtp_config.php) ou envio autenticado pelo domínio
     emorphosis.com.br com Reply-To para emergentmetamorphosis@gmail.com.
   ========================================================================== */

const EMORPHOSIS_PROJECT_EMAIL = 'emergentmetamorphosis@gmail.com';
const EMORPHOSIS_SENDER_NAME   = 'Emergent Metamorphosis';

function emorphosis_send_primary_email(string $toEmail, string $subjectText, string $plainTextBody): bool {
    $projectEmail = EMORPHOSIS_PROJECT_EMAIL;
    $senderName   = EMORPHOSIS_SENDER_NAME;

    // Codifica assunto em UTF-8
    $encodedSubject = '=?UTF-8?B?' . base64_encode($subjectText) . '?=';
    $encodedSender  = '=?UTF-8?B?' . base64_encode($senderName . ' (' . $projectEmail . ')') . '?=';

    // Verifica se há credencial SMTP do Gmail configurada em api/storage/smtp_config.php
    $smtpConfigFile = __DIR__ . '/storage/smtp_config.php';
    if (is_file($smtpConfigFile)) {
        $smtpCfg = include $smtpConfigFile;
        if (is_array($smtpCfg) && !empty($smtpCfg['gmail_app_password'])) {
            $ok = emorphosis_smtp_gmail_send(
                $projectEmail,
                (string)$smtpCfg['gmail_app_password'],
                $senderName,
                $toEmail,
                $encodedSubject,
                $plainTextBody
            );
            if ($ok) {
                return true;
            }
        }
    }

    // Envio com autenticação SPF/DKIM do domínio emorphosis.com.br + Reply-To emergentmetamorphosis@gmail.com
    // Usamos endereço pessoal do projeto (sem "noreply" e sem HTML de marketing) para cair na Caixa Principal (Primary)
    $domainAddress = 'emergentmetamorphosis@emorphosis.com.br';
    $messageId = sprintf('<%s.%s@emorphosis.com.br>', bin2hex(random_bytes(8)), time());

    $headers = [
        'Date: ' . date('r'),
        'Message-ID: ' . $messageId,
        'From: ' . $encodedSender . ' <' . $domainAddress . '>',
        'Reply-To: ' . $senderName . ' <' . $projectEmail . '>',
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
    ];

    return @mail(
        $toEmail,
        $encodedSubject,
        $plainTextBody,
        implode("\r\n", $headers),
        '-f ' . $domainAddress
    );
}

function emorphosis_smtp_gmail_send(
    string $gmailUser,
    string $appPassword,
    string $senderName,
    string $toEmail,
    string $encodedSubject,
    string $plainTextBody
): bool {
    $fp = @stream_socket_client('ssl://smtp.gmail.com:465', $errno, $errstr, 10);
    if (!$fp) {
        return false;
    }

    $read = static function ($fp): string {
        $data = '';
        while ($str = fgets($fp, 515)) {
            $data .= $str;
            if (isset($str[3]) && $str[3] === ' ') {
                break;
            }
        }
        return $data;
    };

    $write = static function ($fp, string $cmd): void {
        fwrite($fp, $cmd . "\r\n");
    };

    $read($fp);
    $write($fp, 'EHLO emorphosis.com.br');
    $read($fp);
    $write($fp, 'AUTH LOGIN');
    $read($fp);
    $write($fp, base64_encode($gmailUser));
    $read($fp);
    $write($fp, base64_encode($appPassword));
    $authResp = $read($fp);
    if (strpos($authResp, '235') === false) {
        fclose($fp);
        return false;
    }

    $write($fp, 'MAIL FROM:<' . $gmailUser . '>');
    $read($fp);
    $write($fp, 'RCPT TO:<' . $toEmail . '>');
    $read($fp);
    $write($fp, 'DATA');
    $read($fp);

    $encodedFromName = '=?UTF-8?B?' . base64_encode($senderName) . '?=';
    $msg = implode("\r\n", [
        'Date: ' . date('r'),
        'From: ' . $encodedFromName . ' <' . $gmailUser . '>',
        'Reply-To: ' . $encodedFromName . ' <' . $gmailUser . '>',
        'To: <' . $toEmail . '>',
        'Subject: ' . $encodedSubject,
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
        '',
        $plainTextBody,
        '.',
    ]);
    $write($fp, $msg);
    $dataResp = $read($fp);
    $write($fp, 'QUIT');
    fclose($fp);

    return strpos($dataResp, '250') !== false;
}
