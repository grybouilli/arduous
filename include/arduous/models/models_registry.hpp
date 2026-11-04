#pragma once

#include <arduous/api/arduous_plugin_api.hpp>
#include <arduous/models/convtasnet/convtasnet.hpp>
#include <arduous/models/convtasnet/streamable_cln_convtasnet.hpp>
#include <arduous/models/convtasnet/streamable_convtasnet.hpp>

static arduous::Factory::Register<arduous::StreamableConvtasnet>    stream_convtasnet_reg("StreamableConvtasnet");
static arduous::Factory::Register<arduous::StreamableCLNConvtasnet> stream_cln_convtasnet_reg(
    "StreamableCLNConvtasnet");
static arduous::Factory::Register<arduous::Convtasnet> stream_offline_convtasnet_reg("Convtasnet");
