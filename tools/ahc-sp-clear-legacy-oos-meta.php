<?php
/**
 * One-shot removal of obsolete Woo post meta from the superseded 24h shared
 * OOS design. Safe to preview. Requires WP-CLI and an existing database backup.
 *
 * Usage (from WordPress root):
 *   wp --require=/absolute/path/ahc-sp-clear-legacy-oos-meta.php ahc stock clear-legacy-oos
 *   wp --require=/absolute/path/ahc-sp-clear-legacy-oos-meta.php ahc stock clear-legacy-oos --execute
 *
 * Never automatically runs on page loads. Does not touch current stock flags,
 * product/variation IDs, SKUs, orders, or the purchase data source.
 */
if (!defined('WP_CLI') || !WP_CLI || !class_exists('WP_CLI')) {
    return;
}
WP_CLI::add_command('ahc stock clear-legacy-oos', function ($args, $assoc_args) {
    global $wpdb;
    $meta_key = '_ahc_inline_oos_until';
    $rows = $wpdb->get_results($wpdb->prepare(
        "SELECT meta_id, post_id FROM {$wpdb->postmeta} WHERE meta_key = %s ORDER BY meta_id",
        $meta_key
    ));
    if (!is_array($rows)) {
        WP_CLI::error('Unable to enumerate legacy metadata. Nothing changed.');
        return;
    }
    $count = count($rows);
    if (!isset($assoc_args['execute'])) {
        WP_CLI::log("DRY RUN: {$count} obsolete 24-hour SOLD OUT mark(s) found; no changes.");
        WP_CLI::log('After a verified database backup, run again with --execute to remove only this exact meta key.');
        return;
    }
    $removed = 0;
    foreach ($rows as $row) {
        if (delete_metadata_by_mid('post', (int)$row->meta_id)) {
            $removed++;
        } else {
            WP_CLI::warning('Could not remove legacy meta_id '.(int)$row->meta_id);
        }
    }
    if ($removed !== $count) {
        WP_CLI::error("Incomplete cleanup: {$removed}/{$count} removed. Inspect warnings and retry.");
        return;
    }
    WP_CLI::success("Removed {$removed} obsolete shared SOLD OUT marks. No Woo stock flags were changed.");
});
