#!/usr/bin/env python3
"""
Test script to extract the "Standing Out" post and verify formatting preservation
"""

from post_extractor import PostExtractor


def test_standing_out_post():
    extractor = PostExtractor()

    # URL for the "Standing Out" post
    test_url = "http://markforster.squarespace.com/blog/2017/7/25/standing-out.html"

    print(f"Testing content extraction with: {test_url}")
    post_data = extractor.extract_single_post(test_url)

    if post_data:
        print(f"\n✅ Successfully extracted post:")
        print(f"   Title: {post_data['title']}")
        print(f"   Author: {post_data['author']}")
        print(f"   Date: {post_data['date']}")
        print(f"   Categories: {post_data['categories']}")
        print(f"   Comments: {post_data['comments_count']}")
        print(f"   Content length: {len(post_data['content'])} chars")

        print("\n" + "=" * 80)
        print("EXTRACTED CONTENT:")
        print("=" * 80)
        print(post_data["content"])
        print("=" * 80)

        # Save the test post
        success = extractor.save_post_data(post_data, "test_output")
        if success:
            print(f"\n💾 Saved to test_output/posts/2017/7/25/standing-out/")
    else:
        print("❌ Failed to extract post content")


if __name__ == "__main__":
    test_standing_out_post()
