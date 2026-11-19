<?php
/**
 * EMORPHOSIS — Modelo de Configuração Privada (Hostinger / Local)
 * Copie este arquivo para api/config.php (ignorado no Git) ou deixe
 * scripts/deploy_ftp.py gerá-lo automaticamente a partir do .env.
 */
declare(strict_types=1);

return [
    'ADMIN_DROP_TOKEN'   => getenv('ADMIN_DROP_TOKEN') ?: '',
    'ADMIN_NOTIFY_EMAIL' => getenv('ADMIN_NOTIFY_EMAIL') ?: '',
    'DROP_RADAR_SECRET'  => getenv('DROP_RADAR_SECRET') ?: '',
    'PRESENCE_SID_SALT'  => getenv('PRESENCE_SID_SALT') ?: '',
    'PRESENCE_IP_SALT'   => getenv('PRESENCE_IP_SALT') ?: '',
];
