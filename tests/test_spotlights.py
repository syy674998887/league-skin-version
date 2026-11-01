import unittest

from league_skin_version import spotlights as s


def video(number, title):
    return {"id": f"{number:011d}", "title": title}


class SpotlightTests(unittest.TestCase):
    def test_title_formats_exclude_other_games_and_collections(self):
        self.assertEqual(s.parse_title("Frostblade Irelia League of Legends Skin Spotlight"), ("Frostblade Irelia", False))
        self.assertEqual(s.parse_title("New Ahri Skin Spotlight - Pre-Release - PBE Preview - League of Legends"), ("New Ahri", True))
        self.assertIsNone(s.parse_title("Frostblade Irelia Wild Rift Skin Spotlight" + " - TFT"))
        self.assertIsNone(s.parse_title("Irelia Skins Spotlight 2026 | League of Legends"))
        self.assertIsNone(s.parse_title("Frostblade Irelia Skin Spotlight Comparison"))

    def test_newest_full_video_wins_over_preview_and_old_release(self):
        skins = [{"name": "Frostblade Irelia"}]
        data = s.catalog([
            video(1, "Frostblade Irelia (2018 Rework) Skin Spotlight - Pre-Release - League of Legends"),
            video(2, "Frostblade Irelia (2018) Skin Spotlight - League of Legends"),
            video(3, "Frostblade Irelia League of Legends Skin Spotlight"),
        ])
        s.attach_spotlights(skins, data)
        self.assertEqual(skins[0]["spotlight"]["videoId"], video(2, "")["id"])
        self.assertFalse(skins[0]["spotlight"]["preview"])

    def test_editions_punctuation_and_missing_records(self):
        skins = [{"name": name} for name in ["Prestige K/DA Ahri", "Prestige K/DA Ahri (2022)", "K/DA Kai’Sa", "K/DA Kai’Sa Special Edition", "No Video"]]
        data = s.catalog([video(1, "Prestige K/DA Ahri (2022) Skin Spotlight - League of Legends"),
                          video(2, "K/DA Kai'Sa Skin Spotlight - Pre-Release - League of Legends")])
        s.attach_spotlights(skins, data)
        self.assertNotIn("spotlight", skins[0])
        self.assertIn("spotlight", skins[1])
        self.assertTrue(skins[2]["spotlight"]["preview"])
        self.assertNotIn("spotlight", skins[3])
        self.assertNotIn("spotlight", skins[4])
        s.attach_spotlights([skins[0]], data)
        self.assertNotIn("spotlight", skins[0])
        lower = s.catalog([video(3, "prestige K/DA Ahri (2022) Skin Spotlight - League of Legends")])
        s.attach_spotlights([skins[0]], lower)
        self.assertNotIn("spotlight", skins[0])

    def test_ambiguous_skin_names_and_bad_ids_are_not_linked(self):
        skins = [{"name": "New Ahri"}, {"name": "New Ahri"}]
        s.attach_spotlights(skins, s.catalog([video(1, "New Ahri Skin Spotlight")]))
        self.assertTrue(all("spotlight" not in skin for skin in skins))
        with self.assertRaises(ValueError):
            s.catalog([{"id": "https://example.com", "title": "New Ahri Skin Spotlight"}])
        with self.assertRaises(ValueError):
            s.attach_spotlights(skins, {"channelId": "other", "videos": []})

    def test_feed_merge_decodes_titles_keeps_history_and_is_idempotent(self):
        old = s.catalog([video(1, "Old Ahri Skin Spotlight")])
        xml = f'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
        <yt:channelId>{s.CHANNEL_ID}</yt:channelId><entry><yt:channelId>{s.CHANNEL_ID}</yt:channelId>
        <yt:videoId>00000000002</yt:videoId><title>New Nunu &amp; Willump Skin Spotlight</title></entry></feed>'''
        merged = s.merge_feed(old, xml)
        self.assertEqual(len(merged["videos"]), 2)
        self.assertEqual(merged["videos"][0]["title"], "New Nunu & Willump Skin Spotlight")
        self.assertEqual(s.merge_feed(merged, xml), merged)
        self.assertEqual(s.merge_feed(merged, xml.replace(f"<yt:channelId>{s.CHANNEL_ID}</yt:channelId>", f"<yt:channelId>{s.CHANNEL_ID[2:]}</yt:channelId>", 1)), merged)
        with self.assertRaises(ValueError):
            s.merge_feed(old, xml.replace(s.CHANNEL_ID, "wrong-channel"))
        self.assertEqual(len(old["videos"]), 1)


if __name__ == "__main__":
    unittest.main()
