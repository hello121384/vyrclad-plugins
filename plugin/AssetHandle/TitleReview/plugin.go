package plugin

import (
	"github.com/Autumn-27/ScopeSentry-Scan/internal/options"
	"github.com/Autumn-27/ScopeSentry-Scan/internal/types"
)

func GetName() string  { return "TitleReview" }
func Install() error   { return nil }
func Check() error     { return nil }
func Uninstall() error { return nil }

func Execute(input interface{}, op options.PluginOption) (interface{}, error) {
	asset, ok := input.(*types.AssetHttp)
	if !ok || asset.Title != "" {
		return nil, nil
	}
	tag := op.Parameter
	if tag == "" {
		tag = "缺少页面标题"
	}
	for _, existing := range asset.Tags {
		if existing == tag {
			return nil, nil
		}
	}
	asset.Tags = append(asset.Tags, tag)
	return nil, nil
}
