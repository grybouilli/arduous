#pragma once

#include <arduous/api/arduous_plugin_api.hpp>
#include <arduous/models/convtasnet/streamable_convtasnet.hpp>

static arduous::Factory::Register<arduous::StreamableConvtasnet> stream_convtasnet_reg("StreamableConvtasnet");
